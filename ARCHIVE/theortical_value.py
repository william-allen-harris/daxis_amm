from ARCHIVE.montecarlo import MonteCarlo
import math
import pandas as pd


def calc_liquidity(amount0, amount1, currentprice, lowerprice, upperprice):
    """Calculate the liquidity for a LP."""
    upper = math.sqrt(upperprice)
    lower = math.sqrt(lowerprice)
    cprice = math.sqrt(currentprice)

    if cprice <= lower:
        return amount0 * (upper * lower) / (upper - lower)

    elif lower < cprice <= upper:
        liquidity0 = amount0 * (upper * cprice ) / (upper - cprice)
        liquidity1 = amount1 / (cprice - lower)
        return min(liquidity0, liquidity1)
    
    elif upper < cprice:
        return amount1 / (upper - lower)

print(calc_liquidity(0.12, 513.34, 4029.63, 3635.7, 4443.81, 6, 18))

def price_to_tick(price, decimals0, decimals1) -> dict:
    return math.floor(math.log(1/price * (10**decimals1) / (10**decimals0)) / math.log(1.0001))


def tick_to_price(tick: str, decimals0, decimals1) -> dict:
    token0_price =  1.0001**(int(tick)) * (10**decimals0) / (10**decimals1)
    return {'token0_price': token0_price, 'token1_price': 1/token0_price}


def build_ticks(tick_list, decimals0, decimals1, fee_tier):
    """
    The input tick_data from the Uniswap_v3 subgraph is scaled by the two tokens decimals.

    Thus:
        L = Liquidity_{from sub-graph} * 10 ^^ (decimals0-decimals1).
    
    To get in the same form as the return value for calc_liquidity multiple all liquidity values by 10 ^^ (decimals0-decimals1).
    https://atiselsts.github.io/pdfs/uniswap-v3-liquidity-math.pdf
    """
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
    df['Liquidity'] = df['Liquidity'] * 10**(decimals0-decimals1)
    return df


def tv(pool, lowerprice, upperprice, amount0, amount1):
    ohlc = pool.OHLC_df.copy().iloc[-3*24:]

    average_hr_fees = pool.volumeUSD * (pool.FeeTier/1000000) / 24

    liquidity = calc_liquidity(amount1, amount0, pool.token0Price, lowerprice, upperprice, pool.t0decimals, pool.t1decimals)
    ticks = build_ticks(pool.Ticks_df.sort_values("tickIdx", ascending=False).to_dict('records'), pool.t0decimals, pool.t1decimals, pool.FeeTier)
    tick_index = ticks.to_dict('index')
    print(liquidity)

    import numpy as np
    import plotly.express as px

    bar_plot = ticks.copy()
    bar_plot.reset_index(inplace=True)
    bar_plot['color'] = np.where((bar_plot['tickIdx'] > pool.tick) & (bar_plot['tickIdx'] < pool.tick + {10000: 200, 3000: 60, 500: 10}[pool.FeeTier]), 'crimson', 'lightslategray')
    bar_plot['diff'] = (bar_plot['Price1']/pool.token0Price) - 1
    bar_plot = bar_plot[bar_plot['diff'].between(3000, 7000)]
    bar_plot.sort_values("Price1", inplace=True)
    fig = px.bar(bar_plot, x="Price1", y='Liquidity', color='color')
    fig.show()


    simulator = MonteCarlo()
    simulator.sim(ohlc)
    #simulator.line_graph()
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
        
        upper = math.sqrt(upperprice * 10**pool.t0decimals / 10**pool.t1decimals)
        lower = math.sqrt(lowerprice * 10**pool.t0decimals / 10**pool.t1decimals)
        cprice = math.sqrt(last_price * 10**pool.t0decimals / 10**pool.t1decimals)

        if cprice <= lower:
            amt1_lp = liquidity * ((1/lower) - (1/upper)) 
            amt0_lp = 0
        
        elif lower < cprice <= upper:
            amt1_lp = liquidity * ((1/cprice) - (1/upper))
            amt0_lp = liquidity * (cprice - lower) 
    
        elif upper < cprice:
            amt1_lp = 0
            amt0_lp = liquidity * (upper - lower)
        
        print(pool.token0Price, last_price, amt0_lp, amt1_lp)
        Ils.append((amt0_lp)*1/last_price +  amt1_lp)

    return sum([sum(fee) + Il for Il, fee in zip(Ils, fees)]) / len(simulator.simulations_dict) 
