from montecarlo import MonteCarlo
import math
import pandas as pd


def calc_liquidity(amount0, amount1, currentprice, lowerprice, upperprice):
    amount0 = amount0 * 10**18
    amount1 = amount1 * 10**6

    upper = math.sqrt(upperprice * 10**6 / 10**18) * 2**96
    lower = math.sqrt(lowerprice * 10**6 / 10**18) * 2**96
    cprice = math.sqrt(currentprice * 10**6 / 10**18) * 2**96

    if cprice <= lower:
        return amount0 * (upper * lower / 2**96) / (upper - lower)

    elif lower < cprice <= upper:
        liquidity0 = amount0 * (upper * cprice / 2**96) / (upper - cprice)
        liquidity1 = amount1 * 2**96 / (cprice - lower)
        return min(liquidity0, liquidity1)
    
    elif upper < cprice:
        return amount1 * 2**96 / (upper - lower)


def price_to_tick(price, decimals0, decimals1) -> dict:
    return math.floor(math.log(1/price * (10**decimals1) / (10**decimals0)) / math.log(1.0001))


def tick_to_price(tick: str, decimals0, decimals1) -> dict:
    token0_price =  1.0001**(int(tick)) * (10**decimals0) / (10**decimals1)
    return {'token0_price': token0_price, 'token1_price': 1/token0_price}


def build_ticks(tick_list, decimals0, decimals1, fee_tier):
    for i in range(len(tick_list)):
        if i == 0:
            tick_list[i]['liquidity'] = int(tick_list[i]['liquidityGross'])
        else:
            tick_list[i]['liquidity'] = tick_list[i-1]['liquidity'] - int(tick_list[i]['liquidityNet'])

    tick_index = {int(tick['tickIdx']): int(tick['liquidity']) for tick in tick_list}
    tick_list = []
    for tick in range(min(tick_index), max(tick_index), {10000: 200, 3000: 60, 500: 10}[fee_tier]):
        prices = tick_to_price(tick, decimals0, decimals1)
        liquidity = tick_index[tick] if tick in tick_index else tick_list[-1][3]
        tick_list.append([tick, prices['token0_price'], prices['token1_price'], liquidity])
    
    df = pd.DataFrame(tick_list, columns=['tickIdx', 'Price0', 'Price1', 'Liquidity'])
    df.set_index('tickIdx', inplace=True)
    return df


def tv(pool, lowerprice, upperprice, amount0, amount1):
    ohlc = pool.OHLC_df.copy().iloc[-3*24:]

    average_hr_fees = pool.volumeUSD * (pool.FeeTier/1000000) / 24

    liquidity = calc_liquidity(amount0, amount1, pool.token0Price, lowerprice, upperprice)
    ticks = build_ticks(pool.Ticks_df.to_dict('records'), pool.t0decimals, pool.t1decimals, pool.FeeTier)
    tick_index = ticks.to_dict('index')

    simulator = MonteCarlo()
    simulator.sim(ohlc)
    fees = []
    for col in simulator.simulations_dict:
        col_fees = []
        for node in simulator.simulations_dict[col]:
            tick = price_to_tick(node, pool.t0decimals, pool.t1decimals)
            closest_tick_spacing = tick - tick % {10000: 200, 3000: 60, 500: 10}[pool.FeeTier]
            tick_liquidity = tick_index[closest_tick_spacing]['Liquidity']
            average_fee_revenue = (liquidity/tick_liquidity) * average_hr_fees
            col_fees.append(average_fee_revenue)
        fees.append(col_fees)
    
    Ils = []
    for col in simulator.simulations_dict:
        last_price = simulator.simulations_dict[col][-1]
        
        upper = math.sqrt(upperprice * 10**6 / 10**18) * 2**96
        lower = math.sqrt(lowerprice * 10**6 / 10**18) * 2**96
        cprice = math.sqrt(1/last_price * 10**6 / 10**18) * 2**96

        if cprice <= lower:
            amt0_lp = liquidity / (upper * lower / 2**96) * (upper - lower) / 10**18
            amt1_lp = 0
        
        elif lower < cprice <= upper:
            amt0_lp = liquidity / (upper * cprice / 2**96) * (upper - cprice) / 10**18
            amt1_lp = liquidity / 2**96 * (cprice - lower) / 10**6
    
        elif upper < cprice:
            amt1_lp = liquidity / 2**96 * (upper - lower)/ 10**6
            amt0_lp = 0

        Ils.append((amt0_lp- amount0)*1/last_price +  amt1_lp - amount1)
    
    return sum([sum(fee) + Il for Il, fee in zip(Ils, fees)]) / len(simulator.simulations_dict) 
