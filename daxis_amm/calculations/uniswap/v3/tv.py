"""
Module defining the Uniswap V3 Theoretical Value Calculators.
"""
from dataclasses import dataclass as _dataclass
from typing import Any as _Any

import pandas as _pd
from toolz import get_in as _get_in

from daxis_amm.calculations.base import BaseCalculator as _BaseCalculator
from daxis_amm.calculations.uniswap.v3 import utils as _utils
from daxis_amm.calculations.uniswap.v3.deposit_amounts import (
    UniswapV3DepositAmountsCalculator as _UniswapV3DepositAmountsCalculator,
)
from daxis_amm.graphs.uniswap.v3.graph import UniswapV3Graph as _UniswapV3Graph


@_dataclass
class UniswapV3TVCalculator(_BaseCalculator):
    """UniswapV3TVCalculator calculates the Theoretical Value of the LP.

    :param start_date: Timestamp of the start date for calculations
    :type start_date: int
    :param value_date: Timestamp of the value date for calculations
    :type value_date: int
    :param simulator: Simulator used for calculations
    :type simulator: Any
    """

    start_date: int
    value_date: int
    simulator: _Any

    def get_data(self) -> dict:
        """Retrieves the necessary data for calculations.

        :return: Dictionary containing all necessary data for calculations
        :rtype: dict
        """
        start_date = self.value_date - (5 * 24 * 60 * 60)
        funcs = {
            "ohlc_hour_df": _UniswapV3Graph.get_pool_hour_data_info(self.position.pool.id, start_date, self.value_date),
            "ohlc_day_df": _UniswapV3Graph.get_pool_day_data_info(self.position.pool.id, start_date, self.value_date),
            "ticks_df": _UniswapV3Graph.get_pool_ticks_info(self.position.pool.id),
            "token_0_hour_df": _UniswapV3Graph.get_token_hour_data_info(
                self.position.pool.token_0.id, start_date, self.value_date
            ),
        }
        return _UniswapV3Graph.run(funcs)

    def stage_data(self, data: dict) -> dict:
        """Stages the data for calculation.

        :param data: Dictionary containing all necessary data for calculations
        :type data: dict
        :return: Dictionary containing staged data for calculations
        :rtype: dict
        """
        average_day_fees = data["ohlc_day_df"]["FeesUSD"].mean()

        ticks = _utils.expand_ticks(
            data["ticks_df"],
            self.position.pool.token_0.decimals,
            self.position.pool.token_1.decimals,
            self.position.pool.fee_tier,
        )
        tick_index = ticks.to_dict("index")

        time_delta = int((self.value_date - self.start_date) / (60 * 60 * 24))

        price_sim = self.simulator.sim(
            data["ohlc_hour_df"]["Close"].iloc[-1], 0.0, data["ohlc_hour_df"]["Close"].std() / 100, time_delta
        )
        price_usd_sim = self.simulator.sim(
            data["token_0_hour_df"]["Close"].iloc[-1], 0.0, data["token_0_hour_df"]["Close"].std() / 100, time_delta
        )

        price = data["ohlc_hour_df"].set_index("psUnix").loc[self.value_date]["Close"]
        token_0_lowerprice = price * (1 - self.position.min_percentage)
        token_0_upperprice = price * (1 + self.position.max_percentage)

        amount0, amount1 = _UniswapV3DepositAmountsCalculator(position=self.position, date=self.value_date).run()
        liquidity = _utils.calculate_liquidity(
            amount0,
            amount1,
            self.position.pool.token_0.decimals,
            self.position.pool.token_1.decimals,
            price,
            token_0_lowerprice,
            token_0_upperprice,
        )

        return {
            "average_day_fees": average_day_fees,
            "tick_index": tick_index,
            "price_sim": price_sim,
            "price_usd_sim": price_usd_sim,
            "liquidity": liquidity,
            "token_0_lowerprice": token_0_lowerprice,
            "token_0_upperprice": token_0_upperprice,
        }

    def calculation(self, staged_data: dict) -> pd.DataFrame:
        """Calculates the theoretical values based on the staged data.

        :param staged_data: Dictionary containing staged data for calculations
        :type staged_data: dict
        :return: Dataframe containing the calculated theoretical values
        :rtype: pd.DataFrame
        """
        fees = []
        deposit_amounts_usd = []

        for col in staged_data["price_sim"]:
            # Calculate the Accrued Fees.
            col_fees = []
            for node in staged_data["price_sim"][col]:
                tick = _utils.price_to_tick(node, self.position.pool.token_0.decimals, self.position.pool.token_1.decimals)
                closest_tick_spacing = tick - tick % _utils.tick_spacing(self.position.pool.fee_tier)
                tick_liquidity = _get_in([closest_tick_spacing, "Liquidity"], staged_data["tick_index"], 0.0)
                average_fee_revenue = (
                    (staged_data["liquidity"] / (tick_liquidity + staged_data["liquidity"]))
                    * staged_data["average_day_fees"]
                    / 24
                )
                col_fees.append(average_fee_revenue)
            fees.append(sum(col_fees))

            # Calculate the Imperminant Loss.
            last_price = staged_data["price_sim"][col].iloc[-1]
            x_delta, y_delta = _utils.amounts_delta(
                staged_data["liquidity"],
                last_price,
                staged_data["token_0_lowerprice"],
                staged_data["token_0_upperprice"],
                self.position.pool.token_0.decimals,
                self.position.pool.token_1.decimals,
            )

            # Convert to USD
            sim_liq = (x_delta + y_delta * last_price) * staged_data["price_usd_sim"][col].iloc[-1]
            deposit_amounts_usd.append(sim_liq)

        tvs = [fee + imp for imp, fee in zip(deposit_amounts_usd, fees)]

        return _pd.DataFrame({"Fees USD": fees, "Deposit Amounts USD": deposit_amounts_usd, "TV": tvs})
