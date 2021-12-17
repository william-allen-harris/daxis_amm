"""
Module defining all Uniswap V3 functions used to complete calculations.
"""
import math
from typing import Tuple

import pandas as pd


def deposit_amount(price_current: float,
                   price_low: float,
                   price_high: float,
                   amount: float,
                   amount_position: str = 'X') -> Tuple[float, float]:
    """
    Calculate the deposit amounts of a uniswap v3 liquidity position.

    NOTE: Price == Token0Price -> Price is in terms of 1 token0 is equal to 'price' of token1.
    Example, WETHUSDC -> Token0Price = $4000 -> for 1 WETH is equal to $4000 USDC.
    """
    sqrt_upper = math.sqrt(price_high)
    sqrt_lower = math.sqrt(price_low)
    sqrt_price = math.sqrt(price_current)

    if amount_position == 'Y':
        liquidity = amount * sqrt_price * \
            sqrt_upper / (sqrt_upper - sqrt_price)

    elif amount_position == 'X':
        liquidity = amount / (sqrt_price - sqrt_lower)

    else:
        raise Exception('Amount position must be either "x" or "y".')

    if sqrt_lower >= sqrt_price:
        amt1_lp = liquidity * ((1/sqrt_lower) - (1/sqrt_upper))
        amt0_lp = 0.0

    elif sqrt_lower < sqrt_price <= sqrt_upper:
        amt1_lp = liquidity * ((1/sqrt_price) - (1/sqrt_upper))
        amt0_lp = liquidity * (sqrt_price - sqrt_lower)

    elif sqrt_upper < sqrt_price:
        amt1_lp = 0.0
        amt0_lp = liquidity * (sqrt_upper - sqrt_lower)

    else:
        raise Exception("Error in sqrt price comparison.")

    return amt0_lp, amt1_lp


def lp_pool_value(liquidity: float, price_current: float, price_low: float, price_high: float) -> float:
    """
    Calculate the value of a uniswap v3 liquidity position in terms of asset Y.

    https://medium.com/auditless/impermanent-loss-in-uniswap-v3-6c7161d3b445
    """
    term_1 = 2 * liquidity * math.sqrt(price_current)
    term_2 = liquidity * (math.sqrt(price_low) + (price_current / math.sqrt(price_high)))
    return term_1 - term_2


def calculate_liquidity(amount_x: float,
                        amount_y: float,
                        price_current: float,
                        price_low: float,
                        price_high: float) -> float:
    """
    Calculate the liquidity for a LP.
    """
    upper = math.sqrt(price_high)
    lower = math.sqrt(price_low)
    cprice = math.sqrt(price_current)

    if cprice <= lower:
        return amount_x * (upper * lower) / (upper - lower)

    elif lower < cprice <= upper:
        liquidity0 = amount_x * (upper * cprice) / (upper - cprice)
        liquidity1 = amount_y / (cprice - lower)
        return min(liquidity0, liquidity1)

    elif upper < cprice:
        return amount_y / (upper - lower)

    raise Exception("Error in sqrt price comparison.")


def price_to_tick(price: float, decimals_x: int, decimals_y: int) -> int:
    """
    Convert price to a tick.
    """
    return math.floor(math.log(1/price * (10**decimals_y) / (10**decimals_x)) / math.log(1.0001))


def tick_to_price(tick: int, decimals_x: int, decimals_y: int) -> dict[str, float]:
    """
    Convert a tick value to prices.
    """
    token1_price = 1.0001**(tick) * (10**decimals_x) / (10**decimals_y)
    return {'token0_price': 1/token1_price, 'token1_price': token1_price}


def tick_spacing(fee_tier: int) -> int:
    """
    Get the tick spacing for a particular fee_tier.
    """
    return {10000: 200, 3000: 60, 500: 10}[fee_tier]


def build_ticks(ticks_df: pd.DataFrame, decimals_x: int, decimals_y: int, fee_tier: int):
    """
    The input tick_data from the Uniswap_v3 subgraph is scaled by the two tokens decimals.

    Thus:
        L = Liquidity_{from sub-graph} * 10 ** (decimals_x-decimals_y).

    To get in the same form as the return value for calculate_liquidity multiple all liquidity values by 10 ^ (decimals_x-decimals_y).
    https://atiselsts.github.io/pdfs/uniswap-v3-liquidity-math.pdf
    """
    ticks_df = ticks_df.sort_values("tickIdx", ascending=False)
    tick_list = ticks_df.to_dict('records')

    for i in range(len(tick_list)):
        if i == 0:
            tick_list[i]['liquidity'] = int(tick_list[i]['liquidityGross'])
        else:
            tick_list[i]['liquidity'] = tick_list[i-1]['liquidity'] - \
                int(tick_list[i]['liquidityNet'])

    tick_index = {int(tick['tickIdx']): int(tick['liquidity'])
                  for tick in tick_list}
    tick_list = []
    for tick in range(min(tick_index), max(tick_index), tick_spacing(fee_tier)):
        prices = tick_to_price(tick, decimals_x, decimals_y)
        liquidity = tick_index[tick] if tick in tick_index else tick_list[-1][3]
        tick_list.append([tick, prices['token0_price'],
                         prices['token1_price'], liquidity])

    df = pd.DataFrame(tick_list, columns=[
                      'tickIdx', 'Price0', 'Price1', 'Liquidity'])
    df.set_index('tickIdx', inplace=True)
    df['Liquidity'] = df.Liquidity * 10**(decimals_x-decimals_y)
    return df


def tv(
    simulator, ohlc_df, ticks_df, token_0_price, token_0_lowerprice, token_0_upperprice,
        amount0, amount1, volume_usd, fee_tier, t0_decimals, t1_decimals):
    """
    Calcualte the Theoretical value of a Liquidity Position.
    """
    ohlc = ohlc_df.copy().iloc[-3*24:]

    average_hr_fees = volume_usd * (fee_tier/1000000) / 24

    liquidity = calculate_liquidity(
        amount0, amount1, token_0_price, token_0_lowerprice, token_0_upperprice)
    ticks = build_ticks(ticks_df, t0_decimals, t1_decimals, fee_tier)
    tick_index = ticks.to_dict('index')

    simulator.sim(ohlc)
    fees = []
    for col in simulator.simulations_dict:
        col_fees = []
        for node in simulator.simulations_dict[col]:
            tick = price_to_tick(node, t0_decimals, t1_decimals)
            closest_tick_spacing = tick - \
                tick % tick_spacing(fee_tier)
            tick_liquidity = tick_index[closest_tick_spacing]['Liquidity']
            average_fee_revenue = (liquidity/tick_liquidity) * average_hr_fees
            col_fees.append(average_fee_revenue)
        fees.append(col_fees)

    Ils = []
    for col in simulator.simulations_dict:
        last_price = simulator.simulations_dict[col][-1]
        sim_liq = lp_pool_value(liquidity, last_price,
                                token_0_lowerprice, token_0_upperprice)
        Ils.append(sim_liq)

    return sum([sum(fee) + Il for Il, fee in zip(Ils, fees)]) / len(simulator.simulations_dict)


def liquidity_graph(ticks_df, token_0_price, tick, fee_tier):
    """
    Create a graph of liquidity.
    """
    import numpy as np
    bar_plot = ticks_df.copy()
    bar_plot.reset_index(inplace=True)
    bar_plot = bar_plot[bar_plot['Price0'].between(
        token_0_price*0.75, token_0_price*1.25)]
    bar_plot['color'] = np.where((bar_plot['tickIdx'] > tick) &
                                 (bar_plot['tickIdx'] < tick + tick_spacing(fee_tier)),
                                 'crimson', 'lightslategray')
    import plotly.graph_objs as go
    data = [go.Bar(
        x=bar_plot['Price0'].values,
        y=bar_plot['Liquidity'].values,
        marker_color=bar_plot['color'].values
    )]
    fig = go.Figure(data=data)
    import plotly.io as pio

    pio.show(fig)
