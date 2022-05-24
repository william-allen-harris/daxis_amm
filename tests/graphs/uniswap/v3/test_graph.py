"""
Module for testing Uniswap V3 Graphs.
"""
from unittest import IsolatedAsyncioTestCase

from daxis_amm.graphs.uniswap.v3.graph import UniswapV3Graph


class TestUniswapV3Graph(IsolatedAsyncioTestCase):
    """
    Tests for Uniswap V3 Graph.

    TODO: Remove dependecy external DB for testing. Introduce a MockDB.
    """

    def setUp(self):
        self.graph = UniswapV3Graph

    async def test_get_static_pool_info(self):
        return_value = await self.graph.get_static_pool_info("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640")
        self.assertEqual(return_value["pool"]["id"], "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640")
        self.assertEqual(return_value["pool"]["token0"]["decimals"], "6")
        self.assertEqual(return_value["pool"]["token1"]["symbol"], "WETH")
