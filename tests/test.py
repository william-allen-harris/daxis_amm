from numpy import sqrt
from daxis_amm.enums import Stables
from daxis_amm.graphs.GetFrames import GetFrames, GetIDs
from daxis_amm.positions.uniswap_v3 import UniswapV3LP

#test_ids = GetIDs(10, 0, 'dict')
#stables = ["USDTUSDC"] #[el.value for el in Stables]
#test_id = [value for key, value in test_ids.items() if all([stable not in key for stable in stables])]

pools = GetFrames(GetIDs(1, 0), return_type='Object')

for pool in pools:
    print(f'Trying to calculate {pool} ....')
    print(pool.std)
    max_price = pool.token0Price + pool.std * sqrt(24)
    min_price = pool.token0Price - pool.std * sqrt(24)

    lp = UniswapV3LP(pool, 1000, min_price, max_price)
    theoretical_value = lp.tv(return_type='breakdown')

    print(f'{lp} - TV: {theoretical_value.mean().to_dict()}')
