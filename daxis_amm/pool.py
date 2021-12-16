"""
Module defining the Uniswap V3 Pool Class.
"""
from dataclasses import dataclass
from pandas import DataFrame

from daxis_amm.calculations import uniswap_v3
from daxis_amm.calculations import montecarlo


@dataclass
class Pool:
    """
    Class representing a Uniswap V3 Pool.
    """
    poolID: str
    liquidity: str
    FeeTier: int
    sqrtPrice: str
    t0id: str
    t0symbol: str
    t0decimals: int
    t1id: str
    t1symbol: str
    t1decimals: int
    feeGrowthGlobal0X128: str
    feeGrowthGlobal1X128: str
    token0Price: float
    token1Price: float
    tick: int
    observationIndex: str
    volumeToken0: str
    volumeToken1: str
    volumeUSD: float
    untrackedVolumeUSD: str
    feesUSD: str
    txCount: str
    collectedFeesToken0: str
    collectedFeesToken1: str
    collectedFeesUSD: str
    liquidityProviderCount: str
    totalValueLockedUSD: str
    totalValueLockedETH: str
    totalValueLockedToken0: str
    totalValueLockedToken1: str
    OHLC_df: DataFrame
    Ticks_df: DataFrame

    def __str__(self):
        return f'Uniswap V3 Pool -> {self.t0symbol}/{self.t1symbol} {self.FeeTier/10000}%'

    def __repr__(self):
        return f'Uniswap V3 Pool: {self.t0symbol}/{self.t1symbol} {self.FeeTier/10000}%'


@dataclass
class UniswapV3LP:
    "Class defining a Uniswap V3 Liquidity Position."
    pool: Pool
    amount: float
    token_0_min_price: float
    token_0_max_price: float
    amount_position: str = 'X'

    def deposit_amounts(self):
        "Calculate the deposit amounts for each token."
        return uniswap_v3.deposit_amount(
            self.pool.token0Price, self.token_0_min_price, self.token_0_max_price, self.amount,
            self.amount_position)

    def tv(self, simulator=montecarlo.MonteCarlo()):
        "Calculate the Theorical Value of the LP."
        amount0, amount1 = self.deposit_amounts()
        return uniswap_v3.tv(simulator, self.pool.OHLC_df, self.pool.Ticks_df, self.pool.
                             token0Price, self.token_0_min_price, self.token_0_max_price, amount0,
                             amount1, self.pool.volumeUSD, self.pool.FeeTier, self.pool.t0decimals,
                             self.pool.t1decimals)

    def built_ticks(self):
        "Build the cumulative ticks dataframe."
        return uniswap_v3.build_ticks(
            self.pool.Ticks_df, self.pool.t0decimals, self.pool.t1decimals, self.pool.FeeTier)

    def graph_liquidity(self):
        "Graph the liquidity"
        uniswap_v3.liquidity_graph(self.built_ticks(), self.pool.token0Price)

