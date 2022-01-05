"Uniswap V3 Theoretical Value calculator."
import pandas as pd

from daxis_amm.enums import Stables
from daxis_amm.calculations.base import BaseCalculator
from daxis_amm.graphs.uniswap_v3.uniswap_v3 import (
    get_pool_hour_data_info,
    get_pool_day_data_info,
    get_pool_ticks_info,
    get_token_hour_data_info,
)
from daxis_amm.calculations.uniswap.v3 import utils


class UniswapV3PnLCalculator(BaseCalculator):
    start_date: int
    end_date: int

    def _get_data(self):
        self.data = {
            "token0_day_usd_price_df": get_token_hour_data_info(
                self.position.pool.t0id, self.start_date, self.end_date
            ).set_index("psUnix"),
            "token1_day_usd_price_df": get_token_hour_data_info(
                self.position.pool.t1id, self.start_date, self.end_date
            ).set_index("psUnix"),
            "ohlc_hour_df": get_pool_hour_data_info(self.position.pool.poolID, self.start_date, self.end_date).set_index(
                "psUnix"
            ),
            "ohlc_day_df": get_pool_day_data_info(self.position.pool.poolID, self.start_date, self.end_date).set_index("Date"),
            "ticks_df": get_pool_ticks_info(self.position.pool.poolID),
            "token_0_hour_df": get_token_hour_data_info(self.position.pool.t0id, self.start_date, self.end_date),
        }

    def _stage_data(self):
        if self.data["ohlc_day_df"].index.max() < self.start_date:
            raise Exception("No OHLC day data available")

        if self.data["ohlc_hour_df"].index.max() < self.start_date:
            raise Exception("No OHLC hour data available")

        first_price = self.data["ohlc_hour_df"].loc[self.start_date]["Close"]
        token_0_lowerprice = first_price * (1 - self.position.min_percentage)
        token_0_upperprice = first_price * (1 + self.position.max_percentage)

        last_price = self.data["ohlc_hour_df"].loc[self.end_date]["Close"]
        usd_x = self.data["token0_day_usd_price_df"].loc[self.end_date]["Close"]
        usd_y = self.data["token1_day_usd_price_df"].loc[self.end_date]["Close"]

        amount0, amount1 = utils.get_deposit_amounts(
            1 / first_price, 1 / token_0_upperprice, 1 / token_0_lowerprice, usd_x, usd_y, self.position.amount
        )

        low = self.data["ohlc_hour_df"]["Low"].min()
        high = self.data["ohlc_hour_df"]["High"].max()

        tick_high = utils.price_to_tick(high, self.position.pool.t0decimals, self.position.pool.t1decimals)
        tick_low = utils.price_to_tick(low, self.position.pool.t0decimals, self.position.pool.t1decimals)
        ticks = utils.expand_ticks(
            self.data["ticks_df"], self.position.pool.t0decimals, self.position.pool.t1decimals, self.position.pool.FeeTier
        )
        ticks = ticks[(ticks.index <= tick_low) & (ticks.index >= tick_high)]

        average_liquidity = ticks.Liquidity.mean()
        liquidity = utils.calculate_liquidity(
            amount0,
            amount1,
            self.position.pool.t0decimals,
            self.position.pool.t1decimals,
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
        # Fees
        accrued_fees = self.staged_data["total_fees"] * (
            self.staged_data["liquidity"] / (self.staged_data["liquidity"] + self.staged_data["average_liquidity"])
        )

        accrued_fees = 0.0 if pd.isna(accrued_fees) else accrued_fees

        # Imperminant Loss
        x_delta, y_delta = utils.amounts_delta(
            self.staged_data["liquidity"],
            self.staged_data["last_price"],
            self.staged_data["token_0_lowerprice"],
            self.staged_data["token_0_upperprice"],
            self.position.pool.t0decimals,
            self.position.pool.t1decimals,
        )

        if Stables.has_member_key(self.position.pool.t0symbol):
            sim_liq = x_delta + y_delta * self.staged_data["last_price"]
        elif Stables.has_member_key(self.position.pool.t1symbol):
            sim_liq = x_delta * 1 / self.staged_data["last_price"] + y_delta
        else:
            sim_liq = (x_delta + y_delta * self.staged_data["last_price"]) * self.staged_data["usd_x"]

        self.result = pd.Series(
            {"Fees USD": accrued_fees, "Deposit Amounts USD": sim_liq, "PnL": (accrued_fees + sim_liq - self.position.amount)}
        )
