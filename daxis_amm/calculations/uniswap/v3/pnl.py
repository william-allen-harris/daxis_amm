"""
Module defining the Uniswap V3 PnL Calculators.
"""
from dataclasses import dataclass as _dataclass

import pandas as _pd

from daxis_amm.calculations.base import BaseCalculator as _BaseCalculator
from daxis_amm.calculations.uniswap.v3 import utils as _utils
from daxis_amm.calculations.uniswap.v3.deposit_amounts import (
    UniswapV3DepositAmountsCalculator as _UniswapV3DepositAmountsCalculator,
)
from daxis_amm.enums import Stables as _Stables
from daxis_amm.graphs.uniswap.v3.graph import UniswapV3Graph as _UniswapV3Graph


@_dataclass
class UniswapV3PnLCalculator(_BaseCalculator):
    """UniswapV3PnLCalculator is a class for calculating Uniswap V3 profit and loss.

    :param start_date: Start timestamp for the calculations
    :type start_date: int

    :param end_date: End timestamp for the calculations
    :type end_date: int
    """

    start_date: int
    end_date: int

    def get_data(self) -> dict:
        """Retrieves the necessary data for calculations.

        :return: Dictionary containing all necessary data for calculations
        :rtype: dict
        """
        funcs = {
            "token0_hour_usd_price_df": _UniswapV3Graph.get_token_hour_data_info(
                self.position.pool.token_0.id, self.start_date, self.end_date
            ),
            "ohlc_hour_df": _UniswapV3Graph.get_pool_hour_data_info(self.position.pool.id, self.start_date, self.end_date),
            "ohlc_day_df": _UniswapV3Graph.get_pool_day_data_info(self.position.pool.id, self.start_date, self.end_date),
            "ticks_df": _UniswapV3Graph.get_pool_ticks_info(self.position.pool.id),
        }

        return _UniswapV3Graph.run(funcs)

    def stage_data(self, data: dict) -> dict:
        """Stages the data for calculation.

        :param data: Dictionary containing all necessary data for calculations
        :type data: dict
        :return: Dictionary containing staged data for calculations
        :rtype: dict
        :raises Exception: If no OHLC day data or hour data is available
        """
        data["token0_hour_usd_price_df"] = data["token0_hour_usd_price_df"].set_index("psUnix")
        data["ohlc_hour_df"] = data["ohlc_hour_df"].set_index("psUnix")
        data["ohlc_day_df"] = data["ohlc_day_df"].set_index("Date")

        if data["ohlc_day_df"].index.max() < self.start_date:
            raise Exception("No OHLC day data available")

        if data["ohlc_hour_df"].index.max() < self.start_date:
            raise Exception("No OHLC hour data available")

        first_price = data["ohlc_hour_df"].loc[self.start_date]["Close"]
        token_0_lowerprice = first_price * (1 - self.position.min_percentage)
        token_0_upperprice = first_price * (1 + self.position.max_percentage)

        last_price = data["ohlc_hour_df"].loc[self.end_date]["Close"]
        usd_x = data["token0_hour_usd_price_df"].loc[self.end_date]["Close"]

        amount0, amount1 = _UniswapV3DepositAmountsCalculator(position=self.position, date=self.end_date).run()

        low = data["ohlc_hour_df"]["Low"].min()
        high = data["ohlc_hour_df"]["High"].max()

        tick_high = _utils.price_to_tick(high, self.position.pool.token_0.decimals, self.position.pool.token_1.decimals)
        tick_low = _utils.price_to_tick(low, self.position.pool.token_0.decimals, self.position.pool.token_1.decimals)
        ticks = _utils.expand_ticks(
            data["ticks_df"],
            self.position.pool.token_0.decimals,
            self.position.pool.token_1.decimals,
            self.position.pool.fee_tier,
        )
        ticks = ticks[(ticks.index <= tick_low) & (ticks.index >= tick_high)]

        average_liquidity = ticks.Liquidity.mean()
        liquidity = _utils.calculate_liquidity(
            amount0,
            amount1,
            self.position.pool.token_0.decimals,
            self.position.pool.token_1.decimals,
            first_price,
            token_0_lowerprice,
            token_0_upperprice,
        )
        total_fees = data["ohlc_day_df"]["FeesUSD"].sum()
        return {
            "liquidity": liquidity,
            "average_liquidity": average_liquidity,
            "last_price": last_price,
            "usd_x": usd_x,
            "total_fees": total_fees,
            "token_0_lowerprice": token_0_lowerprice,
            "token_0_upperprice": token_0_upperprice,
        }

    def calculation(self, staged_data: dict) -> _pd.Series:
        """Calculates the profit and loss based on the staged data.

        :param staged_data: Dictionary containing staged data for calculations
        :type staged_data: dict
        :return: Series containing the calculated profit and loss data
        :rtype: pd.Series
        """
        accrued_fees = staged_data["total_fees"] * (
            staged_data["liquidity"] / (staged_data["liquidity"] + staged_data["average_liquidity"])
        )

        accrued_fees = 0.0 if _pd.isna(accrued_fees) else accrued_fees

        # Calculate Imperminant Loss
        x_delta, y_delta = _utils.amounts_delta(
            staged_data["liquidity"],
            staged_data["last_price"],
            staged_data["token_0_lowerprice"],
            staged_data["token_0_upperprice"],
            self.position.pool.token_0.decimals,
            self.position.pool.token_1.decimals,
        )

        # Convert to USD
        if Stables.has_member_key(self.position.pool.token_0.symbol):
            sim_liq = x_delta + y_delta * staged_data["last_price"]
        elif Stables.has_member_key(self.position.pool.token_1.symbol):
            sim_liq = x_delta * 1 / staged_data["last_price"] + y_delta
        else:
            sim_liq = (x_delta + y_delta * staged_data["last_price"]) * staged_data["usd_x"]

        return _pd.Series(
            {"Fees USD": accrued_fees, "Deposit Amounts USD": sim_liq, "PnL": (accrued_fees + sim_liq - self.position.amount)}
        )
