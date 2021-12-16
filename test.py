from GetFrames import GetIDs, GetFrames
from pool import UniswapV3LP


test_id = GetIDs(1, 0)
pools = GetFrames(test_id, return_type='Object')


for pool in pools:
    print(f'Trying to calculate {pool} ....')
    max_price = pool.token0Price*1.10
    min_price = pool.token0Price*0.90
    lp = UniswapV3LP(pool, 100000, min_price, max_price)
    #lp.built_ticks().to_csv("ticks.csv")
    #lp.graph_liquidity()
    #amount_0, amount_1 = lp.deposit_amounts()
    theoretical_value = lp.tv()
    #print(f'{pool} - {amount_0}: {pool.t0symbol} & {amount_1}: {pool.t1symbol} - 24Hr Liquidity estimated return: {theoretical_value}')
