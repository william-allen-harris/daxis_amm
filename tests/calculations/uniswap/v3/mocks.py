"Module for mocked graph classes."
from datetime import datetime
from dataclasses import dataclass

from daxis_amm.positions.base import BasePosition


@dataclass
class MockToken:
    "Class representing a Uniswap V3 Token."
    id: str


@dataclass
class MockPool:
    """
    Class representing a Uniswap V3 Pool.
    """

    id: str
    fee_tier: int
    token_0: MockToken
    token_1: MockToken


@dataclass
class MockUniswapLP(BasePosition):
    pool_id: str
    amount: float
    start_date: datetime
    end_date: datetime
    min_percentage: float
    max_percentage: float
    pool: MockPool = MockPool("test", 0, MockToken("test"), MockToken("test"))

    def tv(self, value_date, simulator, return_type):
        pass

    def pnl(self, value_date):
        pass


@dataclass
class MockUniswapV3Graph:
    @classmethod
    def get_token_hour_data_info(cls, id, start, date):
        return

    @classmethod
    def get_pool_hour_data_info(cls, id, start, date):
        return

    @classmethod
    def get_dynamic_pool_info(cls, id):
        return

    @classmethod
    def run(cls, funcs):
        return
