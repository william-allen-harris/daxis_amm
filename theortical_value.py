from GetFrames import GetIDs, GetFrames
from montecarlo import MonteCarlo
import math


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

def price_to_tick(price: int, decimals0, decimals1) -> dict:
    return math.floor(math.log(1/price * (10**decimals1) / (10**decimals0)) / math.log(1.0001))


def tv(ohlc, ticks, volumeUSD, fee_tier, decimals0, decimals1, price, lowerprice, upperprice, amount0, amount1):
    ohlc = ohlc.iloc[-3*24:]

    average_hr_fees = volumeUSD * (fee_tier/1000000) / 24

    liquidity = calc_liquidity(amount0, amount1, price, lowerprice, upperprice)
    tick_index = ticks.to_dict('index')

    simulator = MonteCarlo()
    simulator.sim(ohlc)
    fees = []
    for col in simulator.simulations_dict:
        col_fees = []
        for node in simulator.simulations_dict[col]:
            tick = price_to_tick(node, decimals0, decimals1)
            closest_tick_spacing = tick - tick % {10000: 200, 3000: 60, 500: 10}[fee_tier]
            tick_liquidity = tick_index[closest_tick_spacing]['Liquidity']
            average_fee_revenue = (liquidity/tick_liquidity) * average_hr_fees
            col_fees.append(average_fee_revenue)
        fees.append(col_fees)
    
    print(fees)
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

        print(1/last_price, amt0_lp, amt1_lp)
        Ils.append((amt0_lp- amount0)*1/last_price +  amt1_lp - amount1)
    
    return sum([sum(fee) + Il for Il, fee in zip(Ils, fees)]) / len(simulator.simulations_dict) 


test_id= GetIDs(1, 0)
pool_info_df, ohlc_df_list, ticks_df_list = GetFrames(test_id)

# take the first
pool_info_df = pool_info_df.iloc[0]
ohlc_df = ohlc_df_list[0]
ticks_df = ticks_df_list[0]

print(tv(ohlc_df, ticks_df, pool_info_df['volumeUSD'], pool_info_df['FeeTier'], pool_info_df['t0decimals'], pool_info_df['t1decimals'],
	pool_info_df['token0Price'], pool_info_df['token0Price']*0.5, pool_info_df['token0Price']*1.5, 1000, 0.1))