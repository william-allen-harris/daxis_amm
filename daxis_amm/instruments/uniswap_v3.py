"""
Module defining the Uniswap V3 Pool Class.
"""
from dataclasses import dataclass
from pandas import DataFrame


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
    t0derivedETH: float
    t1id: str
    t1symbol: str
    t1decimals: int
    t1derivedETH: float
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
    feesUSD: float
    txCount: str
    collectedFeesToken0: str
    collectedFeesToken1: str
    collectedFeesUSD: str
    liquidityProviderCount: str
    totalValueLockedUSD: str
    totalValueLockedETH: str
    totalValueLockedToken0: str
    totalValueLockedToken1: str
    ethPriceUSD: float

    def __str__(self):
        return f"Uniswap V3 Pool {self.poolID}: {self.t0symbol}{self.t1symbol} {self.FeeTier/10000}%"

    def __repr__(self):
        return f"Uniswap V3 Pool {self.poolID}: {self.t0symbol}{self.t1symbol} {self.FeeTier/10000}%"

    @property
    def std(self):
        return self.OHLC_df.copy().tail(3 * 24)["Close"].std(ddof=0)
