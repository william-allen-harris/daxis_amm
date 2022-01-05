"""
Module defining the Uniswap V3 Liquidity Position Class.
"""
from dataclasses import dataclass
from math import sqrt
from typing import Optional

from datetime import datetime

from daxis_amm.calculations.uniswap.v3 import utils
from daxis_amm.calculations import montecarlo
from daxis_amm.calculations.uniswap.v3.tv import UniswapV3TVCalculator
from daxis_amm.calculations.uniswap.v3.pnl import UniswapV3PnLCalculator
from daxis_amm.graphs.uniswap_v3.uniswap_v3 import get_pool
from daxis_amm.instruments.uniswap_v3 import Pool


@dataclass
class UniswapV3LP:
    """
    Class defining a Uniswap V3 Liquidity Position.

    Amount in USD.
    """

    pool_id: str
    amount: float
    start_date: datetime
    end_date: datetime
    min_percentage: Optional[float] = None
    max_percentage: Optional[float] = None

    def __post_init__(self):
        self.pool: Pool = get_pool(self.pool_id)

    @property
    def token_0_min_price(self):
        if self.min_percentage is None:
            return self.pool.token0Price - self.pool.std * sqrt(24)

        return self.pool.token0Price * (1 - self.min_percentage)

    @property
    def token_0_max_price(self):
        if self.max_percentage is None:
            return self.pool.token0Price + self.pool.std * sqrt(24)

        return self.pool.token0Price * (1 + self.max_percentage)

    def __str__(self):
        return f"{self.pool}-> Uniswap LP from {self.token_0_min_price} to {self.token_0_max_price}"

    def __repr__(self):
        return f"{self.pool}-> Uniswap LP from {self.token_0_min_price} to {self.token_0_max_price}"

    @property
    def deposit_amounts(self):
        "Calculate the deposit amounts for each token."

        if 0.0 in (self.pool.t0derivedETH, self.pool.t1derivedETH):
            raise Exception("Unable to calcualte deposit amounts; One of the Pool derivedETH values are Zero.")

        usd_x = self.pool.ethPriceUSD * self.pool.t0derivedETH
        usd_y = self.pool.ethPriceUSD * self.pool.t1derivedETH
        amount0, amount1 = utils.get_deposit_amounts(
            1 / self.pool.token0Price, 1 / self.token_0_max_price, 1 / self.token_0_min_price, usd_x, usd_y, self.amount
        )

        if amount0 < 0.0 or amount1 < 0.0:
            raise Exception("Unable to calculate deposit amounts; either amount0 and amount1 is below 0.0")

        return amount0, amount1

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

        return UniswapV3TVCalculator(position=self, simulator=simulator, start_date=start_date, value_date=value_date).run

    def pnl(self, value_date):
        "Calculate profit or loss."
        start_date = int(self.start_date.timestamp())
        end_date = int(self.end_date.timestamp())

        if self.start_date >= value_date:
            return 0.0

        if self.start_date < value_date < self.end_date:
            end_date = int(value_date.timestamp())

        return UniswapV3PnLCalculator(position=self, start_date=start_date, end_date=end_date).run

    def built_ticks(self):
        "Build the cumulative ticks dataframe."
        return utils.expand_ticks(self.pool.Ticks_df, self.pool.t0decimals, self.pool.t1decimals, self.pool.FeeTier)

    def graph_liquidity(self):
        "Graph the liquidity"
        utils.liquidity_graph(self.built_ticks(), self.pool.token0Price, self.pool.tick, self.pool.FeeTier)
