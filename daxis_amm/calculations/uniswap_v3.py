"""
Module defining all Uniswap V3 functions used to complete calculations.
"""
import math
from typing import Tuple

import pandas as pd
import numpy as np
import plotly.io as pio
import plotly.graph_objs as go

from daxis_amm.calculations.montecarlo import MonteCarlo
from daxis_amm.enums import Stables


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
    Calculate the value of a uniswap v3 liquidity position in terms of asset X.

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
        return amount_y * (upper * lower) / (upper - lower)

    if lower < cprice <= upper:
        liquidity0 = amount_y * (upper * cprice) / (upper - cprice)
        liquidity1 = amount_x / (cprice - lower)
        return min(liquidity0, liquidity1)

    if upper < cprice:
        return amount_x / (upper - lower)

    raise Exception("Error in sqrt price comparison.")


def price_to_tick(price: float, decimals_x: int, decimals_y: int) -> int:
    """
    Convert price to a tick.
    """
    return math.floor(math.log(1/price * (10**decimals_y) / (10**decimals_x)) / math.log(1.0001))


def tick_to_price(tick: int, decimals_x: int, decimals_y: int) -> float:
    """
    Convert a tick value to prices. Returns Price1.
    """
    return 1.0001**(tick) * (10**decimals_x) / (10**decimals_y)


def tick_spacing(fee_tier: int) -> int:
    """
    Get the tick spacing for a particular fee_tier.
    """
    return {10000: 200, 3000: 60, 500: 10}[fee_tier]


def build_ticks(ticks_df: pd.DataFrame, token_x: str, token_y: str, decimals_x: int, decimals_y: int, fee_tier: int) -> pd.DataFrame:
    """
    The input tick_data from the Uniswap_v3 subgraph is scaled by the two tokens decimals.

    Thus:
        L = Liquidity_{from sub-graph} * 10 ** (decimals_x-decimals_y).

    To get in the same form as the return value for calculate_liquidity
    multiple all liquidity values by 10 ^ (decimals_x-decimals_y).
    This is subjective to the following symbol token names:
        tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);

    https://github.com/Uniswap/v3-core/blob/main/contracts/UniswapV3Factory.sol#L41
    https://atiselsts.github.io/pdfs/uniswap-v3-liquidity-math.pdf
    """
    ticks_df = ticks_df.sort_values("tickIdx").set_index('tickIdx')
    offset = decimals_x-decimals_y if token_x < token_y else decimals_y-decimals_x
    ticks_df['Liquidity'] = ticks_df.liquidityNet.cumsum() * 10**(offset)
    max_tick = ticks_df.index.max()
    min_tick = ticks_df.index.min()

    tick_range = list(range(min_tick, max_tick, tick_spacing(fee_tier)))
    output_df = pd.DataFrame(tick_range, columns=['tickIdx'])
    output_df['Price1'] = output_df.tickIdx.apply(lambda x: tick_to_price(x, decimals_x, decimals_y))
    output_df['Price0'] = output_df.Price1 ** (-1)
    output_df['Liquidity'] = output_df.tickIdx.map(ticks_df['Liquidity']).ffill()
    output_df.set_index('tickIdx', inplace=True)

    return output_df


def tv(simulator: MonteCarlo,
       ohlc_df: pd.DataFrame,
       ohlc_day_df: pd.DataFrame,
       built_ticks_df: pd.DataFrame,
       token_0_price: float,
       token_0_lowerprice: float,
       token_0_upperprice: float,
       token_0: str,
       token_1: str,
       amount0: float,
       amount1: float,
       fee_tier: int,
       t0_decimals: int,
       t1_decimals: int) -> float:
    """
    Calcualte the Theoretical value of a Liquidity Position.
    """
    ohlc = ohlc_df.copy().tail(3*24)

    average_hr_fees = ohlc_day_df.copy().tail(5)['FeesUSD'].mean()
    liquidity = calculate_liquidity(amount0, amount1, token_0_price, token_0_lowerprice, token_0_upperprice)
    ticks = build_ticks(built_ticks_df, token_0, token_1, t0_decimals, t1_decimals, fee_tier)
    tick_index = ticks.to_dict('index')

    simulator.sim(ohlc)
    # ohlc_day_df.to_csv('/workspaces/daxis_amm/tests/data/ohlc_day_df.csv')
    # ohlc_df.to_csv('/workspaces/daxis_amm/tests/data/ohlc_df.csv')
    # built_ticks_df.to_csv('/workspaces/daxis_amm/tests/data/built_ticks_df.csv')

    fees = []
    imperminant_loss = []

    for col in simulator.simulations_dict:
        
        # Calculate the Accrued Fees.
        col_fees = []
        for node in simulator.simulations_dict[col]:
            tick = price_to_tick(node, t0_decimals, t1_decimals)
            closest_tick_spacing = tick - tick % tick_spacing(fee_tier)
            tick_liquidity = tick_index[closest_tick_spacing]['Liquidity']
            average_fee_revenue = (liquidity/tick_liquidity) * average_hr_fees / 24
            col_fees.append(average_fee_revenue)
        fees.append(sum(col_fees))

        # Calculate the Imperminant Loss.
        last_price = simulator.simulations_dict[col][-1]
        sim_liq = lp_pool_value(liquidity, last_price, token_0_lowerprice, token_0_upperprice)

        if Stables.has_member_key(token_0):
            pass

        elif Stables.has_member_key(token_1):
            sim_liq *= 1/last_price

        else:
            raise Exception("UNABLE TO PRICE NON-STABLE PAIRS!")

        imperminant_loss.append(sim_liq)

    return sum([fee + imp for imp, fee in zip(imperminant_loss, fees)]) / len(simulator.simulations_dict)


def liquidity_graph(built_ticks_df: pd.DataFrame, token_0_price: float, tick: int, fee_tier: int) -> None:
    """
    Create a graph of liquidity.
    """
    bar_plot = built_ticks_df.copy()
    bar_plot.reset_index(inplace=True)
    bar_plot = bar_plot[bar_plot['Price0'].between(
        token_0_price*0.75, token_0_price*1.25)]
    bar_plot['color'] = np.where((bar_plot['tickIdx'] > tick) &
                                 (bar_plot['tickIdx'] < tick + tick_spacing(fee_tier)),
                                 'crimson', 'lightslategray')
    data = [go.Bar(
        x=bar_plot['Price0'].values,
        y=bar_plot['Liquidity'].values,
        marker_color=bar_plot['color'].values
    )]
    fig = go.Figure(data=data)
    pio.show(fig)
