"""
Module defining all Uniswap V3 functions used to complete calculations.
"""
import math
from typing import Tuple

import pandas as pd


def deposit_amount(price: float, price_low: float, price_high: float, amount: float,
                   amount_position: str = 'X') -> Tuple[float, float]:
    """
    Calculate the deposit amounts of a uniswap v3 liquidity position.

    https://ethereum.stackexchange.com/questions/99425/calculate-deposit-amount-when-adding-to-a-liquidity-pool-in-uniswap-v3?fbclid=IwAR1BNSfb7YmWMpaDEubofJ4yTh63i1SuBn60ltpmG1FaKIb_7XsRwVT-sQA

    """
    sqrt_upper = math.sqrt(price_high)
    sqrt_lower = math.sqrt(price_low)
    sqrt_price = math.sqrt(price)

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

    return amt0_lp, amt1_lp


assert deposit_amount(2486.8, 1994.2, 2998.9, 2907.729524805772, 'X') == (
    2907.729524805772, 1.0000000000000016)
assert deposit_amount(2486.8, 1994.2, 2998.9, 1, 'Y') == (
    2907.729524805772, 1.0000000000000016)


def lp_pool_value(liquidity: float, price: float, upper: float, lower: float) -> float:
    """
    Calculate the value of a uniswap v3 liquidity position in terms of asset Y.

    https://medium.com/auditless/impermanent-loss-in-uniswap-v3-6c7161d3b445
    """
    return 2 * liquidity * math.sqrt(price) - liquidity * (math.sqrt(lower) +
                                                           (price / math.sqrt(upper)))


assert lp_pool_value(557.9599554712883, 2486.8, 2998.9,
                     1994.2) == 5394.529524805781


def calc_liquidity(amount0, amount1, currentprice, lowerprice, upperprice):
    """
    Calculate the liquidity for a LP.
    """
    upper = math.sqrt(upperprice)
    lower = math.sqrt(lowerprice)
    cprice = math.sqrt(currentprice)

    if cprice <= lower:
        return amount0 * (upper * lower) / (upper - lower)

    elif lower < cprice <= upper:
        liquidity0 = amount0 * (upper * cprice) / (upper - cprice)
        liquidity1 = amount1 / (cprice - lower)
        return min(liquidity0, liquidity1)

    elif upper < cprice:
        return amount1 / (upper - lower)


assert calc_liquidity(0.12, 513.34, 4029.63, 3635.7,
                      4443.81) == 159.55760383772108


def price_to_tick(price, decimals0, decimals1) -> dict:
    """
    Convert a price value to a tick/
    """
    return math.floor(math.log(1/price * (10**decimals1) / (10**decimals0)) / math.log(1.0001))


def tick_to_price(tick: str, decimals0, decimals1) -> dict:
    """
    Convert a tick value to prices.
    """
    token1_price = 1.0001**(int(tick)) * (10**decimals0) / (10**decimals1)
    return {'token0_price': 1/token1_price, 'token1_price': token1_price}


def build_ticks(ticks_df, decimals0, decimals1, fee_tier):
    """
    The input tick_data from the Uniswap_v3 subgraph is scaled by the two tokens decimals.

    Thus:
        L = Liquidity_{from sub-graph} * 10 ** (decimals0-decimals1).

    To get in the same form as the return value for calc_liquidity multiple all liquidity values by 10 ^ (decimals0-decimals1).
    https://atiselsts.github.io/pdfs/uniswap-v3-liquidity-math.pdf
    """
    tick_list = ticks_df.sort_values(
        "tickIdx", ascending=False).to_dict('records')
    for i in range(len(tick_list)):
        if i == 0:
            tick_list[i]['liquidity'] = int(tick_list[i]['liquidityGross'])
        else:
            tick_list[i]['liquidity'] = tick_list[i-1]['liquidity'] - \
                int(tick_list[i]['liquidityNet'])

    tick_index = {int(tick['tickIdx']): int(tick['liquidity'])
                  for tick in tick_list}
    tick_list = []
    for tick in range(min(tick_index), max(tick_index), {10000: 200, 3000: 60, 500: 10}[fee_tier]):
        prices = tick_to_price(tick, decimals0, decimals1)
        liquidity = tick_index[tick] if tick in tick_index else tick_list[-1][3]
        tick_list.append([tick, prices['token0_price'],
                         prices['token1_price'], liquidity])

    df = pd.DataFrame(tick_list, columns=[
                      'tickIdx', 'Price0', 'Price1', 'Liquidity'])
    df.set_index('tickIdx', inplace=True)
    df['Liquidity'] = df.Liquidity * 10**(decimals0-decimals1)
    return df


def tv(
    simulator, ohlc_df, ticks_df, token_0_price, token_0_lowerprice, token_0_upperprice,
        amount0, amount1, volume_usd, fee_tier, t0_decimals, t1_decimals):
    """
    Calcualte the Theoretical value of a Liquidity Position.
    """
    ohlc = ohlc_df.copy().iloc[-3*24:]

    average_hr_fees = volume_usd * (fee_tier/1000000) / 24

    liquidity = calc_liquidity(
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
                tick % {10000: 200, 3000: 60, 500: 10}[fee_tier]
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


def liquidity_graph(ticks_df, token_0_price):
    """
    Create a graph of liquidity.
    """
    bar_plot = ticks_df.copy()
    bar_plot.reset_index(inplace=True)
    bar_plot = bar_plot[bar_plot['Price0'].between(
        token_0_price*0.75, token_0_price*1.25)]
    import plotly.graph_objs as go
    data = [go.Bar(
        x=bar_plot['Price0'].values,
        y=bar_plot['Liquidity'].values,
    )]
    fig = go.Figure(data=data)
    import plotly.io as pio

    pio.show(fig)
