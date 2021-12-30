"""
Module defining all Uniswap V3 functions used to complete calculations.
"""
import math
from typing import Tuple, Union

from toolz import get_in
import pandas as pd
import numpy as np
import plotly.io as pio
import plotly.graph_objs as go

from daxis_amm.calculations.montecarlo import MonteCarlo
from daxis_amm.enums import Stables


def get_deposit_amounts(
    price_current: float, price_low: float, price_high: float, price_usd_x: float, price_usd_y: float, target_amounts: float
) -> Tuple[float, float]:
    """
    Get the deposit amounts for an LP position

    target_amounts is equal to the total USD value of the two deposits.
    """
    sqrt_upper = math.sqrt(price_high)
    sqrt_lower = math.sqrt(price_low)
    sqrt_price = math.sqrt(price_current)

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
) -> Tuple[float, float]:
    """
    Calculate the value of a uniswap v3 liquidity position.

    https://medium.com/auditless/impermanent-loss-in-uniswap-v3-6c7161d3b445
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
        raise Exception("Error in sqrt price comparison.")

    return x_delta / 10 ** (decimals_x), y_delta / 10 ** (decimals_y)


def price_to_tick(price: float, decimals_x: int, decimals_y: int) -> int:
    """
    Convert price to a tick.
    """
    return math.floor(math.log(1 / price * (10 ** decimals_y) / (10 ** decimals_x)) / math.log(1.0001))


def tick_to_price(tick: int, decimals_x: int, decimals_y: int) -> float:
    """
    Convert a tick value to prices. Returns Price1.
    """
    return 1.0001 ** (tick) * (10 ** decimals_x) / (10 ** decimals_y)


def tick_spacing(fee_tier: int) -> int:
    """
    Get the tick spacing for a particular fee_tier.
    """
    return {10000: 200, 3000: 60, 500: 10, 100: 1}[fee_tier]


def expand_ticks(ticks_df: pd.DataFrame, decimals_x: int, decimals_y: int, fee_tier: int) -> pd.DataFrame:
    """
    The input tick_data from the Uniswap_v3 subgraph is scaled by the two tokens decimals.

    https://github.com/Uniswap/v3-core/blob/main/contracts/UniswapV3Factory.sol#L41
    https://atiselsts.github.io/pdfs/uniswap-v3-liquidity-math.pdf
    """
    ticks_df = ticks_df.sort_values("tickIdx").set_index("tickIdx")
    ticks_df["Liquidity"] = ticks_df.liquidityNet.cumsum()  # * 10**(offset)
    max_tick = ticks_df.index.max()
    min_tick = ticks_df.index.min()

    tick_range = list(range(min_tick, max_tick, tick_spacing(fee_tier)))
    output_df = pd.DataFrame(tick_range, columns=["tickIdx"])
    output_df["Price1"] = output_df.tickIdx.apply(lambda x: tick_to_price(x, decimals_x, decimals_y))
    output_df["Price0"] = output_df.Price1 ** (-1)
    output_df["Liquidity"] = output_df.tickIdx.map(ticks_df["Liquidity"]).ffill()
    output_df.set_index("tickIdx", inplace=True)

    return output_df


def expand_decimals(number, exp):
    "Expand a numbers decimals"
    return number * 10 ** (exp)


def get_sqrt_price_x96(price: float, decimals_x: int, decimals_y: int):
    "Get the Square Root X96 Price."
    token0 = expand_decimals(1 / price, decimals_y)
    token1 = expand_decimals(1, decimals_x)
    return math.sqrt(token0 / token1) * 2 ** (96)


def calculate_liquidity(
    amount_x: float, amount_y: float, decimals_x: int, decimals_y: int, price_current: float, price_low: float, price_high: float
) -> float:
    """
    Calculate the liquidity for a LP.
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

    raise Exception("Error in sqrt price comparison.")


def tv(
    simulator: MonteCarlo,
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
    t1_decimals: int,
    ethPriceUSD: float,
    t0derivedETH: float,
    t1derivedETH: float,
    unix_timestamp: int,
    return_type: str = "sum",
) -> Union[float, pd.DataFrame, None]:
    """
    Calcualte the Theoretical value of a Liquidity Position.
    """
    unix_3_delay = unix_timestamp - (3 * 24 * 60 * 60)
    unix_5_delay = unix_timestamp - (5 * 24 * 60 * 60)
    
    if ohlc_df.psUnix.max() < unix_3_delay:
        raise Exception("No OHLC hour data available")

    ohlc = ohlc_df[(ohlc_df["psUnix"] < unix_timestamp) & (ohlc_df["psUnix"] > unix_3_delay)]

    if ohlc_day_df.Date.max() < unix_5_delay:
        raise Exception("No OHLC day data available")

    average_day_fees = ohlc_day_df[(ohlc_day_df["Date"] < unix_timestamp) & (ohlc_day_df["Date"] > unix_5_delay)][
        "FeesUSD"
    ].mean()

    liquidity = calculate_liquidity(
        amount0, amount1, t0_decimals, t1_decimals, token_0_price, token_0_lowerprice, token_0_upperprice
    )
    ticks = expand_ticks(built_ticks_df, t0_decimals, t1_decimals, fee_tier)
    tick_index = ticks.to_dict("index")

    simulator.sim(ohlc)
    # ohlc_day_df.to_csv('/workspaces/daxis_amm/tests/data/ohlc_day_df.csv')
    # ohlc_df.to_csv('/workspaces/daxis_amm/tests/data/ohlc_df.csv')
    # built_ticks_df.to_csv('/workspaces/daxis_amm/tests/data/built_ticks_df.csv')

    fees = []
    imperminant_loss_usd = []

    for col in simulator.simulations_dict:

        # Calculate the Accrued Fees.
        col_fees = []
        for node in simulator.simulations_dict[col]:
            tick = price_to_tick(node, t0_decimals, t1_decimals)
            closest_tick_spacing = tick - tick % tick_spacing(fee_tier)
            tick_liquidity = get_in([closest_tick_spacing, "Liquidity"], tick_index, 0.0)
            average_fee_revenue = (liquidity / (tick_liquidity + liquidity)) * average_day_fees / 24
            col_fees.append(average_fee_revenue)
        fees.append(sum(col_fees))

        # Calculate the Imperminant Loss.
        last_price = simulator.simulations_dict[col][-1]
        x_delta, y_delta = amounts_delta(liquidity, last_price, token_0_lowerprice, token_0_upperprice, t0_decimals, t1_decimals)

        if Stables.has_member_key(token_0):
            sim_liq = x_delta + y_delta * last_price
        elif Stables.has_member_key(token_1):
            sim_liq = x_delta * 1 / last_price + y_delta
        else:
            # sim_liq = x_delta * ethPriceUSD * t0derivedETH + y_delta * ethPriceUSD * t1derivedETH
            raise Exception("Unable to price non-stable pairs.")

        imperminant_loss_usd.append(sim_liq)
    #print(x_delta, y_delta, last_price, token_0_lowerprice, token_0_upperprice)

    totals = [fee + imp for imp, fee in zip(imperminant_loss_usd, fees)]

    if return_type == "breakdown":
        return pd.DataFrame({"Fees USD": fees, "Imperminant Loss USD": imperminant_loss_usd, "TV": totals}, dtype=np.float64)

    elif return_type == "sum":
        return sum(totals) / len(simulator.simulations_dict)


def liquidity_graph(built_ticks_df: pd.DataFrame, token_0_price: float, tick: int, fee_tier: int) -> None:
    """
    Create a graph of liquidity.
    """
    bar_plot = built_ticks_df.copy()
    bar_plot.reset_index(inplace=True)
    bar_plot = bar_plot[bar_plot["Price0"].between(token_0_price * 0.75, token_0_price * 1.25)]
    bar_plot["color"] = np.where(
        (bar_plot["tickIdx"] > tick) & (bar_plot["tickIdx"] < tick + tick_spacing(fee_tier)), "crimson", "lightslategray"
    )
    data = [go.Bar(x=bar_plot["Price0"].values, y=bar_plot["Liquidity"].values, marker_color=bar_plot["color"].values)]
    fig = go.Figure(data=data)
    pio.show(fig)
