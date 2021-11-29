"""
Module defining the Uniswap V3 Pool Class
"""
from dataclasses import dataclass
from pandas import DataFrame


@dataclass
class Pool:
    """
    Uniswap V3 Pool Class
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
    tick: str
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
