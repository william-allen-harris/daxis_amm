"Uniswap V3 Theoretical Value calculator."
from typing import Any

import pandas as pd
from toolz import get_in

from daxis_amm.calculations.base import BaseCalculator
from daxis_amm.calculations.uniswap.v3.deposit_amounts import UniswapV3DepositAmountsCalculator
from daxis_amm.graphs.uniswap.v3.graph import UniswapV3Graph
from daxis_amm.calculations.uniswap.v3 import utils


class UniswapV3TVCalculator(BaseCalculator):
    start_date: int
    value_date: int
    simulator: Any
    """
    Calculate the Theorical Value of the LP.
    1. Get Market Data
        a. OHLC Day Data -> last 5 days from value date
        b. OHLC Hour Data -> last 5 days from value date
        c. Token0 OHLC Hour Data -> last 5 days from value date
        d. Tick Data -> as at Value data

    2. Calculate Input Values
        a. Average Fees.
        b. Ticks Dictionary.
        c. MonteCarlo simulations from OHLC Hour Data. (periods: value_date - start_date)
        d. MonteCarlo simulations from Token0 USD Hour Data. (periods: value_date - start_date)
        e. Liquidity from LP Position.

    3. Estimate FeesUSD and Deposit Amounts USD as at value date.
    """

    def _get_data(self):
        start_date = self.value_date - (5 * 24 * 60 * 60)
        funcs = {
            "ohlc_hour_df": UniswapV3Graph.get_pool_hour_data_info(self.position.pool.id, start_date, self.value_date),
            "ohlc_day_df": UniswapV3Graph.get_pool_day_data_info(self.position.pool.id, start_date, self.value_date),
            "ticks_df": UniswapV3Graph.get_pool_ticks_info(self.position.pool.id),
            "token_0_hour_df": UniswapV3Graph.get_token_hour_data_info(self.position.pool.token_0.id, start_date, self.value_date),
        }
        self.data = UniswapV3Graph.run(funcs)

    def _stage_data(self):
        average_day_fees = self.data["ohlc_day_df"]["FeesUSD"].mean()

        ticks = utils.expand_ticks(
            self.data["ticks_df"], self.position.pool.token_0.decimals, self.position.pool.token_1.decimals, self.position.pool.fee_tier
        )
        tick_index = ticks.to_dict("index")

        time_delta = int((self.value_date - self.start_date) / (60 * 60))

        price_sim = self.simulator.sim(self.data["ohlc_hour_df"], time_delta)
        price_usd_sim = self.simulator.sim(self.data["token_0_hour_df"], time_delta)
        
        price = self.data["ohlc_hour_df"].set_index('psUnix').loc[self.value_date]["Close"]
        token_0_lowerprice = price * (1 - self.position.min_percentage)
        token_0_upperprice = price * (1 + self.position.max_percentage)

        amount0, amount1 = UniswapV3DepositAmountsCalculator(position=self.position, date=self.value_date).run
        liquidity = utils.calculate_liquidity(
            amount0,
            amount1,
            self.position.pool.token_0.decimals,
            self.position.pool.token_1.decimals,
            price,
            token_0_lowerprice,
            token_0_upperprice,
        )

        self.staged_data = {
            "average_day_fees": average_day_fees,
            "tick_index": tick_index,
            "price_sim": price_sim,
            "price_usd_sim": price_usd_sim,
            "liquidity": liquidity,
            "token_0_lowerprice": token_0_lowerprice,
            "token_0_upperprice": token_0_upperprice
        }

    def _calculation(self):
        fees = []
        deposit_amounts_usd = []

        for col in self.staged_data["price_sim"]:

            # Calculate the Accrued Fees.
            col_fees = []
            for node in self.staged_data["price_sim"][col]:
                tick = utils.price_to_tick(node, self.position.pool.token_0.decimals, self.position.pool.token_1.decimals)
                closest_tick_spacing = tick - tick % utils.tick_spacing(self.position.pool.fee_tier)
                tick_liquidity = get_in([closest_tick_spacing, "Liquidity"], self.staged_data["tick_index"], 0.0)
                average_fee_revenue = (
                    (self.staged_data["liquidity"] / (tick_liquidity + self.staged_data["liquidity"]))
                    * self.staged_data["average_day_fees"]
                    / 24
                )
                col_fees.append(average_fee_revenue)
            fees.append(sum(col_fees))

            # Calculate the Imperminant Loss.
            last_price = self.staged_data["price_sim"][col][-1]
            x_delta, y_delta = utils.amounts_delta(
                self.staged_data["liquidity"],
                last_price,
                self.staged_data["token_0_lowerprice"],
                self.staged_data["token_0_upperprice"],
                self.position.pool.token_0.decimals,
                self.position.pool.token_1.decimals,
            )

            # Convert to USD
            sim_liq = (x_delta + y_delta * last_price) * self.staged_data["price_usd_sim"][col][-1]
            deposit_amounts_usd.append(sim_liq)

        tvs = [fee + imp for imp, fee in zip(deposit_amounts_usd, fees)]

        self.result = pd.DataFrame({"Fees USD": fees, "Deposit Amounts USD": deposit_amounts_usd, "TV": tvs})
