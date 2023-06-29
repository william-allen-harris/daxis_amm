"""
Module defining the Uniswap V3 utility functions.
"""

import math as _m
import typing as _tp

import numpy as _np
import pandas as _pd

import plotly.graph_objs as _go
import plotly.io as _pio


def get_deposit_amounts(
    price_current: float, price_low: float, price_high: float, price_usd_x: float, price_usd_y: float, target_amounts: float
) -> _tp.Tuple[float, float]:
    """Get the deposit amounts for an LP position.

    :param price_current: Current price
    :type price_current: float
    :param price_low: Lower price limit
    :type price_low: float
    :param price_high: Higher price limit
    :type price_high: float
    :param price_usd_x: USD price of X token
    :type price_usd_x: float
    :param price_usd_y: USD price of Y token
    :type price_usd_y: float
    :param target_amounts: Equal to the total USD value of the two deposits.
    :type target_amounts: float
    :return: Tuple containing the calculated deposit amounts
    :rtype: Tuple[float, float]
    """

    sqrt_upper = _m.sqrt(price_high)
    sqrt_lower = _m.sqrt(price_low)
    sqrt_price = _m.sqrt(price_current)

    delta_l = target_amounts / ((sqrt_price - sqrt_lower) * price_usd_y + (1 / sqrt_price - 1 / sqrt_upper) * price_usd_x)

    delta_y = delta_l * (sqrt_price - sqrt_lower)
    if delta_y * price_usd_y < 0:
        delta_y = 0

    if delta_y * price_usd_y > target_amounts:
        delta_y = target_amounts / price_usd_y

    delta_x = delta_l * (1 / sqrt_price - 1 / sqrt_upper)
    if delta_x * price_usd_x < 0:
        delta_x = 0
    if delta_x * price_usd_x > target_amounts:
        delta_x = target_amounts / price_usd_x

    return delta_x, delta_y


def amounts_delta(
    liquidity: float, price_current: float, price_low: float, price_high: float, decimals_x: int, decimals_y: int
) -> _tp.Tuple[float, float]:
    """Calculate the value of a Uniswap v3 liquidity position.

    :param liquidity: The liquidity of the position
    :type liquidity: float
    :param price_current: Current price
    :type price_current: float
    :param price_low: Lower price limit
    :type price_low: float
    :param price_high: Higher price limit
    :type price_high: float
    :param decimals_x: Decimal places for X token
    :type decimals_x: int
    :param decimals_y: Decimal places for Y token
    :type decimals_y: int
    :return: Tuple containing the delta values for x and y
    :rtype: Tuple[float, float]
    :raises Exception: If there is an error in sqrt price comparison
    """
    lower = get_sqrt_price_x96(price_high, decimals_x, decimals_y)
    upper = get_sqrt_price_x96(price_low, decimals_x, decimals_y)
    cprice = get_sqrt_price_x96(price_current, decimals_x, decimals_y)

    if lower >= cprice:
        x_delta = liquidity * (upper - lower) / (upper * lower / 2 ** (96))
        y_delta = 0

    elif lower < cprice <= upper:
        x_delta = liquidity * (upper - cprice) / (cprice * upper / 2 ** (96))
        y_delta = liquidity / 2 ** (96) * (cprice - lower)

    elif upper < cprice:
        x_delta = 0.0
        y_delta = liquidity / 2 ** (96) * (upper - lower)

    else:
        raise ValueError("Error in sqrt price comparison.")

    return x_delta / 10 ** (decimals_x), y_delta / 10 ** (decimals_y)


def price_to_tick(price: float, decimals_x: int, decimals_y: int) -> int:
    """Convert price to a tick.

    :param price: Current price
    :type price: float
    :param decimals_x: Decimal places for X token
    :type decimals_x: int
    :param decimals_y: Decimal places for Y token
    :type decimals_y: int
    :return: The tick corresponding to the given price
    :rtype: int
    """
    return _m.floor(_m.log(1 / price * (10**decimals_y) / (10**decimals_x)) / _m.log(1.0001))


def tick_to_price(tick: int, decimals_x: int, decimals_y: int) -> float:
    """Convert a tick value to prices.

    :param tick: The tick value
    :type tick: int
    :param decimals_x: Decimal places for X token
    :type decimals_x: int
    :param decimals_y: Decimal places for Y token
    :type decimals_y: int
    :return: The price corresponding to the given tick
    :rtype: float
    """
    return 1.0001 ** (tick) * (10**decimals_x) / (10**decimals_y)


def tick_spacing(fee_tier: int) -> int:
    """Get the tick spacing for a particular fee_tier.

    :param fee_tier: The fee tier
    :type fee_tier: int
    :return: The tick spacing for the given fee tier
    :rtype: int
    """
    return {10000: 200, 3000: 60, 500: 10, 100: 1}[fee_tier]


def expand_ticks(ticks_df: _pd.DataFrame, decimals_x: int, decimals_y: int, fee_tier: int) -> _pd.DataFrame:
    """Expand the ticks dataframe.

    :param ticks_df: DataFrame containing tick data
    :type ticks_df: pd.DataFrame
    :param decimals_x: Decimal places for X token
    :type decimals_x: int
    :param decimals_y: Decimal places for Y token
    :type decimals_y: int
    :param fee_tier: The fee tier
    :type fee_tier: int
    :return: Expanded DataFrame
    :rtype: pd.DataFrame
    """
    ticks_df = ticks_df.sort_values("tickIdx").set_index("tickIdx")
    ticks_df["Liquidity"] = ticks_df.liquidityNet.cumsum()
    max_tick = ticks_df.index.max()
    min_tick = ticks_df.index.min()

    tick_range = list(range(min_tick, max_tick, tick_spacing(fee_tier)))
    output_df = _pd.DataFrame(tick_range, columns=["tickIdx"])
    output_df["Price1"] = output_df.tickIdx.apply(lambda x: tick_to_price(x, decimals_x, decimals_y))
    output_df["Price0"] = output_df.Price1 ** (-1)
    output_df["Liquidity"] = output_df.tickIdx.map(ticks_df["Liquidity"]).ffill()
    output_df.set_index("tickIdx", inplace=True)

    return output_df


def expand_decimals(number: float, exp: int) -> float:
    """Expand a numbers decimals.

    :param number: The number
    :type number: int
    :param exp: The exponent to use for expanding decimals
    :type exp: int
    :return: The number with expanded decimals
    :rtype: float
    """
    return number * 10 ** (exp)


def get_sqrt_price_x96(price: float, decimals_x: int, decimals_y: int) -> float:
    """Get sqrt(price) * 2**96.

    :param price: The price
    :type price: float
    :param decimals_x: Decimal places for X token
    :type decimals_x: int
    :param decimals_y: Decimal places for Y token
    :type decimals_y: int
    :return: sqrt(price) * 2**96
    :rtype: float
    """
    token0 = expand_decimals(1 / price, decimals_y)
    token1 = expand_decimals(1, decimals_x)
    return _m.sqrt(token0 / token1) * 2 ** (96)


def calculate_liquidity(
    amount_x: float, amount_y: float, decimals_x: int, decimals_y: int, price_current: float, price_low: float, price_high: float
) -> float:
    """
    Calculate liquidity for a given pool.

    :param decimals_x: Decimal places for X token
    :type decimals_x: int
    :param decimals_y: Decimal places for Y token
    :type decimals_y: int
    :param price_current: The current price of X/Y
    :type price_current: float
    :param price_low: Lower price limit for the graph
    :type price_low: float
    :param price_high: Higher price limit for the graph
    :type price_high: float
    :return: DataFrame with the calculated liquidity
    :rtype: pd.DataFrame
    """
    lower = get_sqrt_price_x96(price_high, decimals_x, decimals_y)
    upper = get_sqrt_price_x96(price_low, decimals_x, decimals_y)
    cprice = get_sqrt_price_x96(price_current, decimals_x, decimals_y)

    amount_x = expand_decimals(amount_x, decimals_x)
    amount_y = expand_decimals(amount_y, decimals_y)

    if cprice <= lower:
        return amount_x * (upper * lower / 2 ** (96)) / (upper - lower)

    if lower < cprice <= upper:
        liquidity0 = amount_x * (upper * cprice / 2 ** (96)) / (upper - cprice)
        liquidity1 = amount_y * 2 ** (96) / (cprice - lower)
        return min(liquidity0, liquidity1)

    if upper < cprice:
        return amount_y * 2 ** (96) / (upper - lower)

    raise ValueError("Error in sqrt price comparison.")


def liquidity_graph(df: _pd.DataFrame, token_0_price: float, tick: int, fee_tier: int) -> None:
    """
    Generate a liquidity graph.

    :param df: DataFrame containing the per tick to liquidity data.
    :type df: pd.DataFrame
    :param token_0_price: the current token 0 price
    :type token_0_price: float
    :param tick: The current tick for the pool
    :type tick: int
    """
    bar_plot = df.copy()
    bar_plot.reset_index(inplace=True)
    bar_plot = bar_plot[bar_plot["Price0"].between(token_0_price * 0.75, token_0_price * 1.25)]
    bar_plot["color"] = _np.where(
        (bar_plot["tickIdx"] > tick) & (bar_plot["tickIdx"] < tick + tick_spacing(fee_tier)), "crimson", "lightslategray"
    )
    data = [_go.Bar(x=bar_plot["Price0"].values, y=bar_plot["Liquidity"].values, marker_color=bar_plot["color"].values)]
    fig = _go.Figure(data=data)
    _pio.show(fig)
