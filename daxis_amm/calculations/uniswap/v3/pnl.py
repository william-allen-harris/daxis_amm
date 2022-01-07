"Uniswap V3 Theoretical Value calculator."
import pandas as pd
from daxis_amm.calculations.uniswap.v3.deposit_amounts import UniswapV3DepositAmountsCalculator

from daxis_amm.enums import Stables
from daxis_amm.calculations.base import BaseCalculator
from daxis_amm.graphs.uniswap.v3.graph import UniswapV3Graph
from daxis_amm.calculations.uniswap.v3 import utils


class UniswapV3PnLCalculator(BaseCalculator):
    start_date: int
    end_date: int

    def _get_data(self):
        funcs = {
            "token0_hour_usd_price_df": UniswapV3Graph.get_token_hour_data_info(
                self.position.pool.token_0.id, self.start_date, self.end_date
            ),
            "ohlc_hour_df": UniswapV3Graph.get_pool_hour_data_info(self.position.pool.id, self.start_date, self.end_date),
            "ohlc_day_df": UniswapV3Graph.get_pool_day_data_info(self.position.pool.id, self.start_date, self.end_date),
            "ticks_df": UniswapV3Graph.get_pool_ticks_info(self.position.pool.id),
        }

        self.data = UniswapV3Graph.run(funcs)

    def _stage_data(self):
        self.data["token0_hour_usd_price_df"] = self.data["token0_hour_usd_price_df"].set_index("psUnix")
        self.data["ohlc_hour_df"] = self.data["ohlc_hour_df"].set_index("psUnix")
        self.data["ohlc_day_df"] = self.data["ohlc_day_df"].set_index("Date")

        if self.data["ohlc_day_df"].index.max() < self.start_date:
            raise Exception("No OHLC day data available")

        if self.data["ohlc_hour_df"].index.max() < self.start_date:
            raise Exception("No OHLC hour data available")

        first_price = self.data["ohlc_hour_df"].loc[self.start_date]["Close"]
        token_0_lowerprice = first_price * (1 - self.position.min_percentage)
        token_0_upperprice = first_price * (1 + self.position.max_percentage)

        last_price = self.data["ohlc_hour_df"].loc[self.end_date]["Close"]
        usd_x = self.data["token0_hour_usd_price_df"].loc[self.end_date]["Close"]

        amount0, amount1 = UniswapV3DepositAmountsCalculator(position=self.position, date=self.end_date).run

        low = self.data["ohlc_hour_df"]["Low"].min()
        high = self.data["ohlc_hour_df"]["High"].max()

        tick_high = utils.price_to_tick(high, self.position.pool.token_0.decimals, self.position.pool.token_1.decimals)
        tick_low = utils.price_to_tick(low, self.position.pool.token_0.decimals, self.position.pool.token_1.decimals)
        ticks = utils.expand_ticks(
            self.data["ticks_df"],
            self.position.pool.token_0.decimals,
            self.position.pool.token_1.decimals,
            self.position.pool.fee_tier,
        )
        ticks = ticks[(ticks.index <= tick_low) & (ticks.index >= tick_high)]

        average_liquidity = ticks.Liquidity.mean()
        liquidity = utils.calculate_liquidity(
            amount0,
            amount1,
            self.position.pool.token_0.decimals,
            self.position.pool.token_1.decimals,
            first_price,
            token_0_lowerprice,
            token_0_upperprice,
        )
        total_fees = self.data["ohlc_day_df"]["FeesUSD"].sum()
        self.staged_data = {
            "liquidity": liquidity,
            "average_liquidity": average_liquidity,
            "last_price": last_price,
            "usd_x": usd_x,
            "total_fees": total_fees,
            "token_0_lowerprice": token_0_lowerprice,
            "token_0_upperprice": token_0_upperprice,
        }

    def _calculation(self):
        # Calculate Accured Fees
        accrued_fees = self.staged_data["total_fees"] * (
            self.staged_data["liquidity"] / (self.staged_data["liquidity"] + self.staged_data["average_liquidity"])
        )

        accrued_fees = 0.0 if pd.isna(accrued_fees) else accrued_fees

        # Calculate Imperminant Loss
        x_delta, y_delta = utils.amounts_delta(
            self.staged_data["liquidity"],
            self.staged_data["last_price"],
            self.staged_data["token_0_lowerprice"],
            self.staged_data["token_0_upperprice"],
            self.position.pool.token_0.decimals,
            self.position.pool.token_1.decimals,
        )

        # Convert to USD
        if Stables.has_member_key(self.position.pool.token_0.symbol):
            sim_liq = x_delta + y_delta * self.staged_data["last_price"]
        elif Stables.has_member_key(self.position.pool.token_1.symbol):
            sim_liq = x_delta * 1 / self.staged_data["last_price"] + y_delta
        else:
            sim_liq = (x_delta + y_delta * self.staged_data["last_price"]) * self.staged_data["usd_x"]

        self.result = pd.Series(
            {"Fees USD": accrued_fees, "Deposit Amounts USD": sim_liq, "PnL": (accrued_fees + sim_liq - self.position.amount)}
        )
