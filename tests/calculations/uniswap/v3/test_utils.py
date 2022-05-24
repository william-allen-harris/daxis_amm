"""
Module for testing Uniswap V3 utility functions.
"""
from unittest import TestCase

import pandas as pd
from pandas.testing import assert_frame_equal

from daxis_amm.calculations.uniswap.v3 import utils


class TestUtils(TestCase):
    "Test all functions in the calculations.utils module."

    def test_deposit_amount(self):
        amounts = utils.get_deposit_amounts(1.0000787101403958, 0.9866973124178464, 1.0093756958693298, 1, 1, 1000)
        self.assertTupleEqual(amounts, (407.4399539418319, 592.560046058168))

        amounts = utils.get_deposit_amounts(4109.95688, 3636.1054998424484, 4781.166379972002, 3688.30, 1, 1000)
        self.assertTupleEqual(amounts, (0.14203989758064778, 476.11424575329676))

    def test_amounts_delta(self):
        "Test Liquidity Position Pool Value."
        current_price = 2486.8
        low_price = 1994.2
        high_price = 2998.9

        test_1 = utils.amounts_delta(557959955471287.3, current_price, low_price, high_price, 6, 18)
        self.assertTupleEqual(test_1, (2907.729524805766, 1.0))

    def test_calculate_liquidity(self):
        "Test calcualte liquidity."
        test_1 = utils.calculate_liquidity(2907.729524805772, 1, 6, 18, 2486.8, 1994.2, 2998.9)
        self.assertEqual(test_1, 557959955471287.3)

        test_1 = utils.calculate_liquidity(513.34, 0.12, 6, 18, 4029.63, 3635.7, 4443.81)
        self.assertEqual(test_1, 159557603837720.66)

    def test_price_to_tick(self):
        "Test Price to Tick - INPUT Price_Y"
        test_1 = utils.price_to_tick(1000, 6, 18)
        self.assertEqual(test_1, 207243)

    def test_tick_to_price(self):
        "Test Tick to Price"
        test_1 = utils.tick_to_price(207243, 6, 18)
        self.assertAlmostEqual(test_1, 1 / 1000)

    def test_tick_spacing(self):
        "Test tick spacing"
        self.assertEqual(utils.tick_spacing(10000), 200)
        self.assertEqual(utils.tick_spacing(3000), 60)
        self.assertEqual(utils.tick_spacing(500), 10)

    def test_expand_ticks(self):
        "Test build ticks"
        ticks_df = pd.read_csv("tests/data/ticks.csv.gz", index_col=0)
        built_ticks_results = pd.read_csv("tests/data/built_ticks_results.csv.gz", index_col=0)

        built_ticks = utils.expand_ticks(ticks_df, 6, 18, 500)
        assert_frame_equal(built_ticks, built_ticks_results, check_dtype=False)
