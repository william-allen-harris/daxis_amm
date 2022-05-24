"""
Module for testing Uniswap V3 Deposit Calculators.
"""
from datetime import datetime
from unittest import TestCase, mock

from daxis_amm.calculations.uniswap.v3.deposit_amounts import UniswapV3DepositAmountsCalculator
from tests.calculations.uniswap.v3.mocks import MockUniswapV3Graph, MockUniswapLP
from tests import helpers


class TestDepositAmounts(TestCase):
    "Test Uniswap v3 deposit amounts calculator."

    def setUp(self):
        self.start = datetime(2022, 5, 1)
        self.end = datetime(2022, 5, 10)
        self.mock_lp_position = MockUniswapLP("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", 10000, self.start, self.end, 0.5, 0.5)
        self.calculator = UniswapV3DepositAmountsCalculator(position=self.mock_lp_position, date=int(self.start.timestamp()))
        self.data = helpers.read_pickle("deposit_amounts_data.pickle")
        self.staged_data = {
            "price_current": 0.00036543662808205285,
            "price_high": 0.0007308732561641057,
            "price_low": 0.0002436244187213686,
            "price_usd_x": 1.0,
            "price_usd_y": 2737.2697594666215,
            "target_amounts": 10000,
        }
        self.mock_calculation_value = (1.0, 1.0)

    @mock.patch("daxis_amm.calculations.uniswap.v3.deposit_amounts.UniswapV3Graph", MockUniswapV3Graph)
    def test_get_data(self):
        self.calculator.get_data()

    def test_stage_data(self):
        self.assertDictEqual(self.calculator.stage_data(self.data), self.staged_data)

    @mock.patch("daxis_amm.calculations.uniswap.v3.deposit_amounts.utils.get_deposit_amounts")
    def test_calculate(self, mock_get_deposit_amounts):
        mock_get_deposit_amounts.return_value = self.mock_calculation_value
        self.assertTupleEqual(self.calculator.calculation(self.staged_data), self.mock_calculation_value)
