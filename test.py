import pandas as pd

from daxis_amm.calculations.uniswap.v3 import utils
from daxis_amm.calculations.montecarlo import MonteCarlo
import json

built_ticks_df = pd.read_csv("tests/data/built_ticks_df.csv", index_col=0)
ohlc_df = pd.read_csv("tests/data/ohlc_df.csv", index_col=0)
token_0_price = 3949.372267704334
token_0_lowerprice = 3554.4350409339004
token_0_upperprice = 4344.309494474767
amount0 = 509.36
amount1 = 0.13
volume_usd = 1093571188.0 * 0.0005
fee_tier = 500
t0_decimals = 6
t1_decimals = 18

class MockMonteCarlo(MonteCarlo):
    "Mock MonteCarlo Simulator"

    def __init__(self) -> None:
        with open('tests/data/simulation_df.json',) as file:
            self.simulations_dict = json.load(file)

    def sim(self, ohlc):
        pass

tv = utils.tv(MockMonteCarlo(), ohlc_df, built_ticks_df, token_0_price, token_0_lowerprice,
                  token_0_upperprice, amount0, amount1, volume_usd, fee_tier, t0_decimals, t1_decimals)
print(tv)
