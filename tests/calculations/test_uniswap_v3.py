"Unit testing"

from unittest import TestCase, skip
import json

import pandas as pd
from pandas.testing import assert_frame_equal

from daxis_amm.calculations import uniswap_v3
from daxis_amm.calculations.montecarlo import MonteCarlo


class MockMonteCarlo(MonteCarlo):
    "Mock MonteCarlo Simulator"

    def __init__(self, name) -> None:
        with open(
            f"tests/data/{name}/simulation_df.json",
        ) as file:
            self.simulations_dict = json.load(file)

    def sim(self, ohlc):
        pass


class TestUniswapV3(TestCase):
    "Test all functions in the calculations.uniswap_v3 module."

    def test_deposit_amount(self):
        amounts = uniswap_v3.get_deposit_amounts(1.0000787101403958, 0.9866973124178464, 1.0093756958693298, 1, 1, 1000)
        self.assertTupleEqual(amounts, (407.4399539418319, 592.560046058168))

        amounts = uniswap_v3.get_deposit_amounts(4109.95688, 3636.1054998424484, 4781.166379972002, 3688.30, 1, 1000)
        self.assertTupleEqual(amounts, (0.14203989758064778, 476.11424575329676))

    def test_amounts_delta(self):
        "Test Liquidity Position Pool Value."
        current_price = 2486.8
        low_price = 1994.2
        high_price = 2998.9

        test_1 = uniswap_v3.amounts_delta(557959955471287.3, current_price, low_price, high_price, 6, 18)
        self.assertTupleEqual(test_1, (2907.729524805766, 1.0))

    def test_calculate_liquidity(self):
        "Test calcualte liquidity."
        test_1 = uniswap_v3.calculate_liquidity(2907.729524805772, 1, 6, 18, 2486.8, 1994.2, 2998.9)
        self.assertEqual(test_1, 557959955471287.3)

        test_1 = uniswap_v3.calculate_liquidity(513.34, 0.12, 6, 18, 4029.63, 3635.7, 4443.81)
        self.assertEqual(test_1, 159557603837720.66)

    def test_price_to_tick(self):
        "Test Price to Tick - INPUT Price_Y"
        test_1 = uniswap_v3.price_to_tick(1000, 6, 18)
        self.assertEqual(test_1, 207243)

    def test_tick_to_price(self):
        "Test Tick to Price"
        test_1 = uniswap_v3.tick_to_price(207243, 6, 18)
        self.assertAlmostEqual(test_1, 1 / 1000)

    def test_tick_spacing(self):
        "Test tick spacing"
        self.assertEqual(uniswap_v3.tick_spacing(10000), 200)
        self.assertEqual(uniswap_v3.tick_spacing(3000), 60)
        self.assertEqual(uniswap_v3.tick_spacing(500), 10)

    def test_expand_ticks(self):
        "Test build ticks"
        ticks_df = pd.read_csv("tests/data/ticks.csv.gz", index_col=0)
        built_ticks_results = pd.read_csv("tests/data/built_ticks_results.csv.gz", index_col=0)

        built_ticks = uniswap_v3.expand_ticks(ticks_df, 6, 18, 500)
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
        token0 = "USDC"
        token1 = "WETH"
        fee_tier = 500
        t0_decimals = 6
        t1_decimals = 18
        ethPriceUSD = 3815.8029979140315
        t0derivedETH = 1 / 3815.8029979140315
        t1derivedETH = 1
        unix_timstamp = 1640768949

        tv = uniswap_v3.tv(
            MockMonteCarlo("usdc_weth_500"),
            ohlc_hour_df,
            ohlc_day_df,
            built_ticks_df,
            token_0_price,
            token_0_lowerprice,
            token_0_upperprice,
            token0,
            token1,
            amount0,
            amount1,
            fee_tier,
            t0_decimals,
            t1_decimals,
            ethPriceUSD,
            t0derivedETH,
            t1derivedETH,
            unix_timstamp,
            "breakdown",
        )
        self.assertAlmostEqual(tv["Fees USD"].mean(), 1.7592059904271529, places=2)
        self.assertAlmostEqual(tv["Deposit Amounts USD"].mean(), 953.1767093262931, places=2)

    def test_tv_token_1_stable(self):
        "Test Theorical Value"

        # TODO: This might be wrong need to use ETH simulation price instead of current.
        built_ticks_df = pd.read_csv("tests/data/weth_usdt_500/built_ticks_df.csv", index_col=0)
        ohlc_hour_df = pd.read_csv("tests/data/weth_usdt_500/ohlc_hour_df.csv", index_col=0)
        ohlc_day_df = pd.read_csv("tests/data/weth_usdt_500/ohlc_day_df.csv", index_col=0)
        token_0_price = 0.0002622689648836899
        token_0_lowerprice = 0.0002360420683953209
        token_0_upperprice = 0.0002884958613720589
        amount0 = 0.1446017094995115
        amount1 = 500.0
        token0 = "WETH"
        token1 = "USDT"
        fee_tier = 500
        t0_decimals = 18
        t1_decimals = 6
        ethPriceUSD = 1 / 0.0002622689648836899
        t0derivedETH = 1
        t1derivedETH = 0.0002622689648836899
        unix_timstamp = 1640768949

        tv = uniswap_v3.tv(
            MockMonteCarlo("weth_usdt_500"),
            ohlc_hour_df,
            ohlc_day_df,
            built_ticks_df,
            token_0_price,
            token_0_lowerprice,
            token_0_upperprice,
            token0,
            token1,
            amount0,
            amount1,
            fee_tier,
            t0_decimals,
            t1_decimals,
            ethPriceUSD,
            t0derivedETH,
            t1derivedETH,
            unix_timstamp,
            "breakdown",
        )
        self.assertAlmostEqual(tv["Fees USD"].mean(), 10.164602227734377, places=2)
        self.assertAlmostEqual(tv["Deposit Amounts USD"].mean(), 1044.6770319594814, places=2)

    @skip("Still need to develop.")
    def test_tv_token_1_etherum(self):
        "Test Theorical Value"
        built_ticks_df = pd.read_csv("tests/data/wbtc_weth_3000/built_ticks_df.csv", index_col=0)
        ohlc_hour_df = pd.read_csv("tests/data/wbtc_weth_3000/ohlc_hour_df.csv", index_col=0)
        ohlc_day_df = pd.read_csv("tests/data/wbtc_weth_3000/ohlc_day_df.csv", index_col=0)
        token_0_price = 0.07928533775940265
        token_0_lowerprice = 1 / 13
        token_0_upperprice = 1 / 12
        amount0 = 0.01
        amount1 = 0.16
        token0 = "WBTC"
        token1 = "WETH"
        fee_tier = 3000
        t0_decimals = 8
        t1_decimals = 18
        ethPriceUSD = 3790.070521531456
        t0derivedETH = 12.612672509948505
        t1derivedETH = 1
        unix_timstamp = 1640768949

        tv = uniswap_v3.tv(
            MockMonteCarlo("wbtc_weth_3000"),
            ohlc_hour_df,
            ohlc_day_df,
            built_ticks_df,
            token_0_price,
            token_0_lowerprice,
            token_0_upperprice,
            token0,
            token1,
            amount0,
            amount1,
            fee_tier,
            t0_decimals,
            t1_decimals,
            ethPriceUSD,
            t0derivedETH,
            t1derivedETH,
            unix_timstamp,
            "breakdown",
        )
        self.assertAlmostEqual(tv["Fees USD"].mean(), 1.0751387330063196, places=2)
        self.assertAlmostEqual(tv["Deposit Amounts USD"].mean(), 976.9403872979935, places=2)
