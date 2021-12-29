"Unit testing"

from unittest import TestCase
import json

import pandas as pd
from pandas.testing import assert_frame_equal

from daxis_amm.calculations import uniswap_v3
from daxis_amm.calculations.montecarlo import MonteCarlo


class MockMonteCarlo(MonteCarlo):
    "Mock MonteCarlo Simulator"

    def __init__(self, name) -> None:
        with open(f'tests/data/{name}/simulation_df.json',) as file:
            self.simulations_dict = json.load(file)

    def sim(self, ohlc):
        pass


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
        test_1 = uniswap_v3.calculate_liquidity(2907.729524805772, 1, 2486.8, 1994.2, 2998.9)
        self.assertEqual(test_1, 557.9599554712883)

        test_1 = uniswap_v3.calculate_liquidity(513.34, 0.12, 4029.63, 3635.7, 4443.81)
        self.assertEqual(test_1, 159.55760383772108)

    def test_price_to_tick(self):
        "Test Price to Tick - INPUT Price_Y"
        test_1 = uniswap_v3.price_to_tick(1000, 6, 18)
        self.assertEqual(test_1, 207243)

    def test_tick_to_price(self):
        "Test Tick to Price"
        test_1 = uniswap_v3.tick_to_price(207243, 6, 18)
        self.assertAlmostEqual(test_1, 1/1000)

    def test_tick_spacing(self):
        "Test tick spacing"
        self.assertEqual(uniswap_v3.tick_spacing(10000), 200)
        self.assertEqual(uniswap_v3.tick_spacing(3000), 60)
        self.assertEqual(uniswap_v3.tick_spacing(500), 10)

    def test_build_ticks(self):
        "Test build ticks"
        ticks_df = pd.read_csv("tests/data/ticks.csv.gz", index_col=0)
        built_ticks_results = pd.read_csv("tests/data/built_ticks_results.csv.gz", index_col=0)
        token0 = 'USDC'
        token1 = 'WETH'

        built_ticks = uniswap_v3.build_ticks(ticks_df, token0, token1, 6, 18, 500)
        assert_frame_equal(built_ticks, built_ticks_results, check_dtype=False)

    def test_tv_token_0_stable(self):
        "Test Theorical Value"
        built_ticks_df = pd.read_csv("tests/data/usdc_weth_500/built_ticks_df.csv", index_col=0)
        ohlc_hour_df = pd.read_csv("tests/data/usdc_weth_500/ohlc_hour_df.csv", index_col=0)
        ohlc_day_df = pd.read_csv("tests/data/usdc_weth_500/ohlc_day_df.csv", index_col=0)
        token_0_price = 3815.8029979140315
        token_0_lowerprice = 3434.2226981226286
        token_0_upperprice = 4197.383297705435
        amount0 = 500.0
        amount1 = 0.11883039444280304
        token0 = 'USDC'
        token1 = 'WETH'
        fee_tier = 500
        t0_decimals = 6
        t1_decimals = 18

        tv = uniswap_v3.tv(MockMonteCarlo('usdc_weth_500'), ohlc_hour_df, ohlc_day_df, built_ticks_df, token_0_price,
                           token_0_lowerprice, token_0_upperprice, token0, token1, amount0, amount1, fee_tier, t0_decimals, t1_decimals)
        self.assertAlmostEqual(tv, 954.9359388210878)

    def test_tv_token_1_stable(self):
        "Test Theorical Value"
        built_ticks_df = pd.read_csv("tests/data/weth_usdt_500/built_ticks_df.csv", index_col=0)
        ohlc_hour_df = pd.read_csv("tests/data/weth_usdt_500/ohlc_hour_df.csv", index_col=0)
        ohlc_day_df = pd.read_csv("tests/data/weth_usdt_500/ohlc_day_df.csv", index_col=0)
        token_0_price = 0.0002622689648836899
        token_0_lowerprice = 0.0002360420683953209
        token_0_upperprice = 0.0002884958613720589
        amount0 = 0.1446017094995115
        amount1 = 500.0
        token0 = 'WETH'
        token1 = 'USDT'
        fee_tier = 500
        t0_decimals = 18
        t1_decimals = 6

        tv = uniswap_v3.tv(MockMonteCarlo('weth_usdt_500'), ohlc_hour_df, ohlc_day_df, built_ticks_df, token_0_price,
                           token_0_lowerprice, token_0_upperprice, token0, token1, amount0, amount1, fee_tier, t0_decimals, t1_decimals)
        self.assertAlmostEqual(tv, 1054.844324697902)
