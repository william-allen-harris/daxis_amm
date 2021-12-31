from daxis_amm.calculations.montecarlo import BrownianMotion
from daxis_amm.enums import Stables
from daxis_amm.graphs.GetFrames import GetIDs
from daxis_amm.positions.uniswap_v3 import UniswapV3LP

import logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.ERROR)

def get_pair_id(token0, token1):
    test_ids = GetIDs(100, 0, "dict")
    stables = [token0, token1]
    return [value for key, value in test_ids.items() if all([stable in key for stable in stables])]


def get_first_ids_that_have_stable_pairs(first):
    test_ids = GetIDs(first, 0, "dict")
    stables = [el.value for el in Stables]
    return [value for key, value in test_ids.items() if any([stable in key for stable in stables])]


ids = get_first_ids_that_have_stable_pairs(10)

for id in ids:
    lp = UniswapV3LP(id, 1000)
    print(f"Trying to calculate {lp} ....")

    try:
        theoretical_value = lp.tv(simulator=BrownianMotion())
        print(theoretical_value)
    except Exception as err:
        print(err)
