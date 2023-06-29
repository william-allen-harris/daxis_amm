"""
Module defining the Uniswap V3 Deposit Amount Calculators.
"""
from dataclasses import dataclass as _dataclass
from datetime import datetime as _dt

from daxis_amm.calculations.base import BaseCalculator as _BaseCalculator
from daxis_amm.calculations.uniswap.v3 import utils as _utils
from daxis_amm.graphs.uniswap.v3.graph import UniswapV3Graph as _UniswapV3Graph


@_dataclass
class UniswapV3DepositAmountsCalculator(_BaseCalculator):
    """UniswapV3DepositAmountsCalculator is a class for calculating Uniswap V3 deposit amounts.

    :param date: Timestamp of the date to use for calculations
    :type date: int

    .. note:: The methods of this class include get_data, stage_data, and calculation.
    """

    date: int

    def get_data(self) -> dict:
        """Retrieves the necessary data for calculations.

        :return: Dictionary containing all necessary data for calculations
        :rtype: dict
        """

        start = self.date - (1 * 60 * 60)

        funcs = {
            "token0_hour_usd_price_df": _UniswapV3Graph.get_token_hour_data_info(self.position.pool.token_0.id, start, self.date),
            "token1_hour_usd_price_df": _UniswapV3Graph.get_token_hour_data_info(self.position.pool.token_1.id, start, self.date),
            "ohlc_hour_df": _UniswapV3Graph.get_pool_hour_data_info(self.position.pool.id, start, self.date),
            "pool_dynamic_data": _UniswapV3Graph.get_dynamic_pool_info(self.position.pool.id),
        }

        return _UniswapV3Graph.run(funcs)

    def stage_data(self, data: dict) -> dict:
        """Stages the data for calculation.

        :param data: Dictionary containing all necessary data for calculations
        :type data: dict
        :return: Dictionary containing staged data for calculations
        :rtype: dict
        """

        if _dt.now().timestamp() - self.date < 60:
            raise NotImplementedError
        else:
            data["token0_hour_usd_price_df"] = data["token0_hour_usd_price_df"].set_index("psUnix")
            data["token1_hour_usd_price_df"] = data["token1_hour_usd_price_df"].set_index("psUnix")
            data["ohlc_hour_df"] = data["ohlc_hour_df"].set_index("psUnix")

            price = data["ohlc_hour_df"].loc[self.date]["Close"]
            token_0_lowerprice = price * (1 - self.position.min_percentage)
            token_0_upperprice = price * (1 + self.position.max_percentage)

            usd_x = data["token0_hour_usd_price_df"].loc[self.date]["Close"]
            usd_y = data["token1_hour_usd_price_df"].loc[self.date]["Close"]

        return {
            "price_current": 1 / price,
            "price_high": 1 / token_0_lowerprice,
            "price_low": 1 / token_0_upperprice,
            "price_usd_x": usd_x,
            "price_usd_y": usd_y,
            "target_amounts": self.position.amount,
        }

    def calculation(self, staged_data: dict) -> tuple:
        """Calculates the deposit amounts based on the staged data.

        :param staged_data: Dictionary containing staged data for calculations
        :type staged_data: dict
        :return: Tuple containing the calculated deposit amounts
        :rtype: tuple
        :raises ValueError: If either of the calculated amounts is below 0.0
        """

        result = _utils.get_deposit_amounts(**staged_data)
        if result[0] < 0.0 or result[1] < 0.0:
            raise ValueError("Unable to calculate deposit amounts; either amount0 and amount1 is below 0.0")
        return result
