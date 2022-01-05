"Uniswap V3 Theoretical Value calculator."
from typing import Any

import pandas as pd
from toolz import get_in

from daxis_amm.calculations.base import BaseCalculator
from daxis_amm.graphs.uniswap_v3.uniswap_v3 import (
    get_pool_hour_data_info,
    get_pool_day_data_info,
    get_pool_ticks_info,
    get_token_hour_data_info,
)
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
        self.data = {
            "ohlc_hour_df": get_pool_hour_data_info(self.position.pool.poolID, start_date, self.value_date),
            "ohlc_day_df": get_pool_day_data_info(self.position.pool.poolID, start_date, self.value_date),
            "ticks_df": get_pool_ticks_info(self.position.pool.poolID),
            "token_0_hour_df": get_token_hour_data_info(self.position.pool.t0id, start_date, self.value_date),
        }

    def _stage_data(self):
        average_day_fees = self.data["ohlc_day_df"]["FeesUSD"].mean()

        ticks = utils.expand_ticks(
            self.data["ticks_df"], self.position.pool.t0decimals, self.position.pool.t1decimals, self.position.pool.FeeTier
        )
        tick_index = ticks.to_dict("index")

        time_delta = int((self.value_date - self.start_date) / (60 * 60))

        price_sim = self.simulator.sim(self.data["ohlc_hour_df"], time_delta)
        price_usd_sim = self.simulator.sim(self.data["token_0_hour_df"], time_delta)

        amount0, amount1 = self.position.deposit_amounts
        liquidity = utils.calculate_liquidity(
            amount0,
            amount1,
            self.position.pool.t0decimals,
            self.position.pool.t1decimals,
            self.position.pool.token0Price,
            self.position.token_0_min_price,
            self.position.token_0_max_price,
        )

        self.staged_data = {
            "average_day_fees": average_day_fees,
            "tick_index": tick_index,
            "price_sim": price_sim,
            "price_usd_sim": price_usd_sim,
            "liquidity": liquidity,
        }

    def _calculation(self):
        fees = []
        deposit_amounts_usd = []

        for col in self.staged_data["price_sim"]:

            # Calculate the Accrued Fees.
            col_fees = []
            for node in self.staged_data["price_sim"][col]:
                tick = utils.price_to_tick(node, self.position.pool.t0decimals, self.position.pool.t1decimals)
                closest_tick_spacing = tick - tick % utils.tick_spacing(self.position.pool.FeeTier)
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
                self.position.token_0_min_price,
                self.position.token_0_max_price,
                self.position.pool.t0decimals,
                self.position.pool.t1decimals,
            )
            sim_liq = (x_delta + y_delta * last_price) * self.staged_data["price_usd_sim"][col][-1]

            deposit_amounts_usd.append(sim_liq)

        tvs = [fee + imp for imp, fee in zip(deposit_amounts_usd, fees)]

        self.result = pd.DataFrame({"Fees USD": fees, "Deposit Amounts USD": deposit_amounts_usd, "TV": tvs})
