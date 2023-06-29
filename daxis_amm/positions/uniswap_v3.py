"""
Module defining the Uniswap V3 Liquidity Position Class.
"""
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from daxis_amm.calculations import montecarlo
from daxis_amm.calculations.uniswap.v3.deposit_amounts import UniswapV3DepositAmountsCalculator
from daxis_amm.calculations.uniswap.v3.tv import UniswapV3TVCalculator
from daxis_amm.calculations.uniswap.v3.pnl import UniswapV3PnLCalculator
from daxis_amm.graphs.uniswap.v3.graph import get_pool
from daxis_amm.instruments.uniswap_v3 import Pool
from daxis_amm.positions.base import BasePosition


@dataclass
class UniswapV3LP(BasePosition):
    """
    Class defining a Uniswap V3 Liquidity Position.

    Amount in USD.
    """

    pool_id: str
    amount: float
    start_date: datetime
    end_date: datetime
    min_percentage: float
    max_percentage: float

    def __post_init__(self):
        """
        Initialize the UniswapV3LP object.

        :return: None
        """
        self.pool: Pool = get_pool(self.pool_id)

    def __str__(self):
        """
        Get the string representation of the UniswapV3LP object.

        :return: String representation of the object.
        :rtype: str
        """
        return f"{self.pool}-> Uniswap LP"

    def __repr__(self):
        """
        Get the string representation of the UniswapV3LP object.

        :return: String representation of the object.
        :rtype: str
        """
        return f"{self.pool}-> Uniswap LP"

    def deposit_amounts(self, date):
        """
        Calculate the deposit amounts for each token.

        :param date: The date for which to calculate the deposit amounts.
        :type date: datetime
        :return: The deposit amounts for each token.
        :rtype: Any
        """
        return UniswapV3DepositAmountsCalculator(position=self, date=date).run()

    def tv(self, value_date, simulator=montecarlo.MonteCarlo(), return_type="sum"):
        """
        Calculate the Theoretical Value of the LP.

        :param value_date: The date at which to calculate the theoretical value.
        :type value_date: datetime
        :param simulator: The Monte Carlo simulator object. Default is montecarlo.MonteCarlo().
        :type simulator: montecarlo.MonteCarlo
        :param return_type: The type of return to calculate. Default is "sum".
        :type return_type: str
        :return: The theoretical value of the LP.
        :rtype: Union[pd.Series, Any]
        """
        # TODO: Need to get ticks for the specific valuation date.

        if value_date >= self.end_date:
            value_date = self.end_date
        else:
            raise Exception("Unable to TV when valuation date is before self.start_date")

        start_date = int(self.start_date.timestamp())
        value_date = int(value_date.timestamp())

        tv = UniswapV3TVCalculator(position=self, simulator=simulator, start_date=start_date, value_date=value_date).run()

        if return_type == "sum":
            return pd.Series({"TV": tv["TV"].mean()})

        return tv

    def pnl(self, value_date):
        """
        Calculate the profit or loss.

        :param value_date: The date at which to calculate the profit or loss.
        :type value_date: datetime
        :return: The profit or loss of the position.
        :rtype: float
        """
        start_date = int(self.start_date.timestamp())
        end_date = int(self.end_date.timestamp())

        if self.start_date >= value_date:
            return 0.0

        if self.start_date < value_date < self.end_date:
            end_date = int(value_date.timestamp())

        return UniswapV3PnLCalculator(position=self, start_date=start_date, end_date=end_date).run()
