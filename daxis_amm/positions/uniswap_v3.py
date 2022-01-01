"""
Module defining the Uniswap V3 Liquidity Position Class.
"""
from dataclasses import dataclass
from math import sqrt
from typing import Optional

from datetime import datetime

from daxis_amm.calculations import uniswap_v3
from daxis_amm.calculations import montecarlo
from daxis_amm.enums import Stables
from daxis_amm.graphs.uniswap_v3 import get_pool, get_token_day_data_info, get_token_hour_data_info
from daxis_amm.instruments.uniswap_v3 import Pool


@dataclass
class UniswapV3LP:
    """
    Class defining a Uniswap V3 Liquidity Position.

    Amount in USD.
    TODO: Simulator needs to be changed to accomidate end_date - start date
    """

    pool_id: str
    amount: float
    start_date: datetime
    end_date: datetime
    min_percentage: Optional[float] = None
    max_percentage: Optional[float] = None

    def __post_init__(self):
        self.pool: Pool = get_pool(self.pool_id)

    @property
    def token_0_min_price(self):
        if self.min_percentage is None:
            return self.pool.token0Price - self.pool.std * sqrt(24)

        return self.pool.token0Price * (1 - self.min_percentage)

    @property
    def token_0_max_price(self):
        if self.max_percentage is None:
            return self.pool.token0Price + self.pool.std * sqrt(24)

        return self.pool.token0Price * (1 + self.max_percentage)

    def __str__(self):
        return f"{self.pool}-> Uniswap LP from {self.token_0_min_price} to {self.token_0_max_price}"

    def __repr__(self):
        return f"{self.pool}-> Uniswap LP from {self.token_0_min_price} to {self.token_0_max_price}"

    @property
    def deposit_amounts(self):
        "Calculate the deposit amounts for each token."

        if 0.0 in (self.pool.t0derivedETH, self.pool.t1derivedETH):
            raise Exception("Unable to calcualte deposit amounts; One of the Pool derivedETH values are Zero.")

        usd_x = self.pool.ethPriceUSD * self.pool.t0derivedETH
        usd_y = self.pool.ethPriceUSD * self.pool.t1derivedETH
        amount0, amount1 = uniswap_v3.get_deposit_amounts(
            1 / self.pool.token0Price, 1 / self.token_0_max_price, 1 / self.token_0_min_price, usd_x, usd_y, self.amount
        )

        if amount0 < 0.0 or amount1 < 0.0:
            raise Exception("Unable to calculate deposit amounts; either amount0 and amount1 is below 0.0")

        return amount0, amount1

    def tv(self, value_date, simulator=montecarlo.MonteCarlo(), return_type="sum"):
        "Calculate the Theorical Value of the LP."
        # TODO: Need to get ticks for the specific valuation date.
        

        if value_date >= self.end_date:
            value_date = self.end_date
        else:
            raise Exception("Unable to TV when valuation date is before self.start_date")
        
        amount0, amount1 = self.deposit_amounts
        value_date_timestamp = int(value_date.timestamp())

        if not any([Stables.has_member_key(self.pool.t0symbol), Stables.has_member_key(self.pool.t1symbol)]):
            unix_3_delay = value_date_timestamp - (3 * 24 * 60 * 60)
            token0_usd_price_df = get_token_hour_data_info(self.pool.t0id, value_date_timestamp).sort_values("psUnix")
            time_filter = (token0_usd_price_df["psUnix"] <= value_date_timestamp) & (token0_usd_price_df["psUnix"] >= unix_3_delay)
            token0_usd_price_df = token0_usd_price_df[time_filter]
            simulator.sim(token0_usd_price_df)
            token_0_usd_simulator_dict = simulator.simulations_dict.copy()

        else:
            token_0_usd_simulator_dict = None

        return uniswap_v3.tv(
            simulator,
            self.pool.OHLC_df,
            self.pool.OHLC_day_df,
            self.pool.Ticks_df,
            self.pool.token0Price,
            self.token_0_min_price,
            self.token_0_max_price,
            self.pool.t0symbol,
            self.pool.t1symbol,
            amount0,
            amount1,
            self.pool.FeeTier,
            self.pool.t0decimals,
            self.pool.t1decimals,
            token_0_usd_simulator_dict,
            value_date_timestamp,
            return_type,
        )

    def pnl(self, value_date=datetime.now()):
        start_unixtime = int(self.start_date.timestamp())
        end_unixtime = int(self.end_date.timestamp())

        token0_day_usd_price_df = get_token_day_data_info(self.pool.t0id).set_index("Date").sort_index()
        token1_day_usd_price_df = get_token_day_data_info(self.pool.t1id).set_index("Date").sort_index()

        return uniswap_v3.pnl(
            start_unixtime,
            end_unixtime,
            self.pool.OHLC_df,
            self.pool.OHLC_day_df,
            self.pool.Ticks_df,  # TODO: This is wrong get ticks df at end date.
            token0_day_usd_price_df,
            token1_day_usd_price_df,
            self.min_percentage,
            self.max_percentage,
            self.pool.t0symbol,
            self.pool.t1symbol,
            self.amount,
            self.pool.FeeTier,
            self.pool.t0decimals,
            self.pool.t1decimals,
        )

    def built_ticks(self):
        "Build the cumulative ticks dataframe."
        return uniswap_v3.expand_ticks(self.pool.Ticks_df, self.pool.t0decimals, self.pool.t1decimals, self.pool.FeeTier)

    def graph_liquidity(self):
        "Graph the liquidity"
        uniswap_v3.liquidity_graph(self.built_ticks(), self.pool.token0Price, self.pool.tick, self.pool.FeeTier)
