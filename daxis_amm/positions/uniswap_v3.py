"""
Module defining the Uniswap V3 Liquidity Position Class.
"""
from dataclasses import dataclass

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

    @property
    def deposit_amounts(self):
        "Calculate the deposit amounts for each token."
        amount_x = self.amount/2 * 1/self.pool.ethPriceUSD * 1/self.pool.t0derivedETH

        return uniswap_v3.deposit_amount(
            self.pool.token0Price, self.token_0_min_price, self.token_0_max_price, amount_x)

    def tv(self, simulator=montecarlo.MonteCarlo()):
        "Calculate the Theorical Value of the LP."
        amount0, amount1 = self.deposit_amounts
        print(self.pool.token0Price, self.token_0_min_price, self.token_0_max_price, self.pool.t0symbol,
              self.pool.t1symbol, amount0, amount1, self.pool.FeeTier, self.pool.t0decimals,
              self.pool.t1decimals, self.pool.ethPriceUSD, self.pool.t0derivedETH)
        return uniswap_v3.tv(simulator, self.pool.OHLC_df, self.pool.OHLC_day_df, self.pool.Ticks_df, self.pool.
                             token0Price, self.token_0_min_price, self.token_0_max_price, self.pool.t0symbol,
                             self.pool.t1symbol, amount0, amount1, self.pool.FeeTier, self.pool.t0decimals,
                             self.pool.t1decimals, self.pool.ethPriceUSD, self.pool.t0derivedETH)

    def built_ticks(self):
        "Build the cumulative ticks dataframe."
        return uniswap_v3.build_ticks(
            self.pool.Ticks_df, self.pool.t0symbol, self.pool.t1symbol,
            self.pool.t0decimals, self.pool.t1decimals, self.pool.FeeTier)

    def graph_liquidity(self):
        "Graph the liquidity"
        uniswap_v3.liquidity_graph(self.built_ticks(), self.pool.token0Price, self.pool.tick, self.pool.FeeTier)
