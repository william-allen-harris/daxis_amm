from daxis_amm.enums import Stables
from daxis_amm.graphs.GetFrames import GetFrames, GetIDs
from daxis_amm.positions.uniswap_v3 import UniswapV3LP

test_id = GetIDs(10, 0)
pools = GetFrames(test_id, return_type='Object')
pools = [pools[6]]

for pool in pools:
    print(f'Trying to calculate {pool} ....')
    max_price = pool.token0Price*1.05
    min_price = pool.token0Price*0.95

    print(pool.ethPriceUSD, pool.t0derivedETH, pool.t1derivedETH)

    lp = UniswapV3LP(pool, 500, min_price, max_price)

    # lp.graph_liquidity()
    theoretical_value = lp.tv()
    print(f'{pool} - {pool.t0symbol}{pool.t1symbol} - LP theorical value: {theoretical_value}')
