"""
Module defining the Uniswap V3 Token/Pool Class.
"""
import dataclasses as _dc


@_dc.dataclass
class Token:
    "Class representing a Uniswap V3 Token."
    id: str
    symbol: str
    name: str
    decimals: int
    total_supply: int


@_dc.dataclass
class Pool:
    """
    Class representing a Uniswap V3 Pool.
    """

    id: str
    fee_tier: int
    token_0: Token
    token_1: Token

    def __str__(self):
        return f"Uniswap V3 Pool {self.id}: {self.token_0.symbol}{self.token_1.symbol} {self.fee_tier/10000}%"

    def __repr__(self):
        return f"Uniswap V3 Pool {self.id}: {self.token_0.symbol}{self.token_1.symbol} {self.fee_tier/10000}%"
