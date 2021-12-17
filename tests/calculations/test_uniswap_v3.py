"Unit testing"

from unittest import TestCase

import pandas as pd
from pandas.testing import assert_frame_equal

from daxis_amm.calculations import uniswap_v3


class TestUniswapV3(TestCase):
    "Test all functions in the calculations.uniswap_v3 module."

    def test_deposit_amount(self):
        "Test deposit amount"
        current_price = 2486.8
        low_price = 1994.2
        high_price = 2998.9
        x_amount = 2907.729524805772
        y_amount = 1
        result = (2907.729524805772, 1.0000000000000016)

        test_1 = uniswap_v3.deposit_amount(current_price, low_price, high_price, x_amount, 'X')
        self.assertTupleEqual(test_1, result)

        test_2 = uniswap_v3.deposit_amount(current_price, low_price, high_price, y_amount, 'Y')
        self.assertTupleEqual(test_2, result)

        test_3 = uniswap_v3.deposit_amount(1/current_price, 1/high_price, 1/low_price, y_amount, 'X')
        self.assertTupleEqual(test_3, (1.0, 2907.7295248057635))

        test_4 = uniswap_v3.deposit_amount(1/current_price, 1/high_price, 1/low_price, x_amount, 'Y')
        self.assertTupleEqual(test_4, (1.0000000000000018, 2907.7295248057685))

    def test_lp_pool_value(self):
        "Test Liquidity Position Pool Value."
        current_price = 2486.8
        low_price = 1994.2
        high_price = 2998.9

        test_1 = uniswap_v3.lp_pool_value(557.9599554712883, current_price, low_price, high_price)
        self.assertEqual(test_1, 5394.529524805781)

    def test_calculate_liquidity(self):
        "Test calcualte liquidity."
        test_1 = uniswap_v3.calculate_liquidity(0.12, 513.34, 4029.63, 3635.7, 4443.81)
        self.assertEqual(test_1, 159.55760383772108)

    def test_price_to_tick(self):
        "Test Price to Tick - INPUT Price_Y"
        test_1 = uniswap_v3.price_to_tick(1000, 6, 18)
        self.assertEqual(test_1, 207243)

    def test_tick_to_price(self):
        "Test Tick to Price"
        test_1 = uniswap_v3.tick_to_price(207243, 6, 18)
        self.assertAlmostEqual(test_1['token0_price'], 1000, 2)
        self.assertAlmostEqual(test_1['token1_price'], 1/1000)

    def test_tick_spacing(self):
        "Test tick spacing"
        self.assertEqual(uniswap_v3.tick_spacing(10000), 200)
        self.assertEqual(uniswap_v3.tick_spacing(3000), 60)
        self.assertEqual(uniswap_v3.tick_spacing(500), 10)

    def test_build_ticks(self):
        "Test build ticks"
        ticks_df: pd.DataFrame = pd.read_csv("tests/data/ticks.csv.gz")
        built_ticks_results = pd.read_csv("tests/data/built_ticks_results.csv.gz", index_col=0)

        built_ticks = uniswap_v3.build_ticks(ticks_df, 6, 18, 500)
        assert_frame_equal(built_ticks, built_ticks_results, check_dtype=False)
