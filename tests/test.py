from daxis_amm.graphs.GetFrames import GetFrames, GetIDs
from daxis_amm.positions.uniswap_v3 import UniswapV3LP

test_id = GetIDs(10, 0)
pools = GetFrames(test_id, return_type='Object')

for pool in pools:
    print(f'Trying to calculate {pool} ....')
    max_price = pool.token0Price*1.10
    min_price = pool.token0Price*0.90
    print(pool.token0Price, max_price, min_price)
    if pool.t0symbol in ('USDT', 'DAI', 'USDC'):
        lp = UniswapV3LP(pool, 500, min_price, max_price, 'X')
    elif pool.t1symbol in ('USDT', 'DAI', 'USDC'):
        lp = UniswapV3LP(pool, 500, min_price, max_price, 'Y')
    else:
        raise Exception("UNABLE TO PRICE NON-STABLE PAIRS!")
    lp.graph_liquidity()
    theoretical_value = lp.tv()
    print(f'{pool} - {pool.t0symbol}{pool.t1symbol} - 24Hr Liquidity estimated return: {theoretical_value}')
