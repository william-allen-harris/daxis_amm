from GetFrames import GetIDs, GetFrames
from theortical_value import tv

import math

test_id= GetIDs(10, 0)
pools = GetFrames(test_id, return_type='Object')

USD_STABLES = ('USDC', 'USDT', 'DAI')

def calcualte_deposit_amounts(pool, total_usd: float, price_low: float, price_high: float):

    if pool.t1symbol in USD_STABLES:
        L = total_usd/2 * math.sqrt(pool.token0Price) * math.sqrt(price_high) / (math.sqrt(price_high) - math.sqrt(pool.token0Price))      
        amount_1 = L * (math.sqrt(pool.token0Price) - math.sqrt(price_low))      
        return amount_1, total_usd/2

    elif pool.t0symbol in USD_STABLES:
        L = total_usd/2 / (math.sqrt(pool.token0Price) - math.sqrt(price_low))
        amount_0 = L * (math.sqrt(price_high) - math.sqrt(pool.token0Price)) / (math.sqrt(pool.token0Price) * math.sqrt(price_high))
        return total_usd/2, amount_0

    raise NotImplemented('Currently can only handle USD stable pools')

for pool in pools:
    print(f'Trying to calculate {pool} ....')
    max_price = pool.token0Price*1.5
    min_price = pool.token0Price*0.5
    amount_0, amount_1 = calcualte_deposit_amounts(pool, 1000, min_price, max_price)
    theoretical_value = tv(pool, min_price, max_price, amount_0, amount_1)
    print(f'{pool} - {amount_0}: {pool.t0symbol} & {amount_1}: {pool.t1symbol} - 24Hr Liquidity estimated return: {theoretical_value}')


### TODO: Pairs with USD stable as token_1 look to be creating strange results.