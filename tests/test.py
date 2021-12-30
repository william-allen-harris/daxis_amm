from numpy import sqrt
from daxis_amm.calculations.montecarlo import BrownianMotion
from daxis_amm.enums import Stables
from daxis_amm.graphs.GetFrames import GetFrames, GetIDs
from daxis_amm.positions.uniswap_v3 import UniswapV3LP


def get_pair_id(token0, token1):
    test_ids = GetIDs(100, 0, "dict")
    stables = [token0, token1]
    return [value for key, value in test_ids.items() if all([stable in key for stable in stables])]


def get_first_ids_that_have_stable_pairs(first):
    test_ids = GetIDs(first, 0, "dict")
    stables = [el.value for el in Stables]
    return [value for key, value in test_ids.items() if any([stable in key for stable in stables])]


ids = get_first_ids_that_have_stable_pairs(3)
pools = GetFrames(GetIDs(5, 0), return_type="Object")

for pool in pools:
    try:
        print(f"Trying to calculate {pool} ....")
        max_price = pool.token0Price + pool.std * sqrt(24)
        min_price = pool.token0Price - pool.std * sqrt(24)

        lp = UniswapV3LP(pool, 1000, min_price, max_price)
        theoretical_value = lp.tv(simulator=BrownianMotion(), return_type="breakdown")
        print(theoretical_value.mean())
    except Exception as err:
        print(err)
