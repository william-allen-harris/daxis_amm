"""
Module defining the Uniswap V3 Liquidity Position Class.
"""
from dataclasses import dataclass

from datetime import datetime

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
        self.pool: Pool = get_pool(self.pool_id)

    def __str__(self):
        return f"{self.pool}-> Uniswap LP"

    def __repr__(self):
        return f"{self.pool}-> Uniswap LP"

    def deposit_amounts(self, date):
        "Calculate the deposit amounts for each token."
        return UniswapV3DepositAmountsCalculator(position=self, date=date).run()

    def tv(self, value_date, simulator=montecarlo.MonteCarlo(), return_type="sum"):
        """
        Calculate the Theorical Value of the LP.
        """
        # TODO: Need to get ticks for the specific valuation date.

        if value_date >= self.end_date:
            value_date = self.end_date
        else:
            raise Exception("Unable to TV when valuation date is before self.start_date")

        start_date = int(self.start_date.timestamp())
        value_date = int(value_date.timestamp())

        return UniswapV3TVCalculator(position=self, simulator=simulator, start_date=start_date, value_date=value_date).run()

    def pnl(self, value_date):
        "Calculate profit or loss."
        start_date = int(self.start_date.timestamp())
        end_date = int(self.end_date.timestamp())

        if self.start_date >= value_date:
            return 0.0

        if self.start_date < value_date < self.end_date:
            end_date = int(value_date.timestamp())

        return UniswapV3PnLCalculator(position=self, start_date=start_date, end_date=end_date).run()

    # def built_ticks(self):
    #    "Build the cumulative ticks dataframe."
    #    return utils.expand_ticks(self.pool.Ticks_df, self.pool.t0decimals, self.pool.t1decimals, self.pool.FeeTier)

    # def graph_liquidity(self):
    #    "Graph the liquidity"
    #    utils.liquidity_graph(self.built_ticks(), self.pool.token0Price, self.pool.tick, self.pool.FeeTier)
