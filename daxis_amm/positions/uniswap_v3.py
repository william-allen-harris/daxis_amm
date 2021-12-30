"""
Module defining the Uniswap V3 Liquidity Position Class.
"""
from dataclasses import dataclass

from datetime import datetime

from daxis_amm.calculations import uniswap_v3
from daxis_amm.calculations import montecarlo
from daxis_amm.instruments.uniswap_v3 import Pool


@dataclass
class UniswapV3LP:
    """
    Class defining a Uniswap V3 Liquidity Position.

    Amount in USD.
    """

    pool: Pool
    amount: float
    token_0_min_price: float
    token_0_max_price: float

    def __str__(self):
        return f"{self.pool}-> Uniswap LP {self.token_0_min_price} to {self.token_0_max_price}"

    def __repr__(self):
        return f"{self.pool}-> Uniswap LP {self.token_0_min_price} to {self.token_0_max_price}"

    @property
    def deposit_amounts(self):
        "Calculate the deposit amounts for each token."

        if 0.0 in (self.pool.t0derivedETH, self.pool.t1derivedETH):
            raise Exception("Unable to calcualte deposit amounts; One of the Pool derivedETH values are Zero.")

        usd_x = self.pool.ethPriceUSD * self.pool.t0derivedETH
        usd_y = self.pool.ethPriceUSD * self.pool.t1derivedETH
        amount0, amount1 = uniswap_v3.get_deposit_amounts(
            1 / self.pool.token0Price, 1 / self.token_0_max_price, 1 / self.token_0_min_price, usd_x, usd_y, self.amount
        )

        if amount0 < 0.0 or amount1 < 0.0:
            raise Exception("Unable to calculate deposit amounts; either amount0 and amount1 is below 0.0")

        return amount0, amount1

    def tv(self, simulator=montecarlo.MonteCarlo(), return_type="sum"):
        "Calculate the Theorical Value of the LP."
        amount0, amount1 = self.deposit_amounts
        date_timestamp = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        return uniswap_v3.tv(
            simulator,
            self.pool.OHLC_df,
            self.pool.OHLC_day_df,
            self.pool.Ticks_df,
            self.pool.token0Price,
            self.token_0_min_price,
            self.token_0_max_price,
            self.pool.t0symbol,
            self.pool.t1symbol,
            amount0,
            amount1,
            self.pool.FeeTier,
            self.pool.t0decimals,
            self.pool.t1decimals,
            self.pool.ethPriceUSD,
            self.pool.t0derivedETH,
            self.pool.t1derivedETH,
            date_timestamp,
            return_type,
        )

    def built_ticks(self):
        "Build the cumulative ticks dataframe."
        return uniswap_v3.expand_ticks(self.pool.Ticks_df, self.pool.t0decimals, self.pool.t1decimals, self.pool.FeeTier)

    def graph_liquidity(self):
        "Graph the liquidity"
        uniswap_v3.liquidity_graph(self.built_ticks(), self.pool.token0Price, self.pool.tick, self.pool.FeeTier)
