from dataclasses import dataclass

import plotly.express as px
import numpy as np
import plotly.graph_objects as go
import math


from base_token import ABCToken, ABCContext


@dataclass
class Token(ABCToken):
    symbol: str
    context: ABCContext

    @property
    def id(self) -> str:
        return self.context.token_id(self.symbol)

    @property
    def name(self) -> str:
        return self.context.token_name(self.symbol)

    @property
    def decimals(self) -> int:
        return self.context.token_decimals(self.symbol)



class Pair:
    def __init__(self, token0_symbol:str, token1_symbol:str, context: 'ABCContext'):
        self.context: 'ABCContext' = context
        self.token0: Token = Token(token0_symbol, self.context)
        self.token1: Token = Token(token1_symbol, self.context)

    @property
    def id(self):
        return self.context.pool_id(self.token0.id, self.token1.id)

    @property
    def volumeUSD(self):
        return self.context.pool_volumeUSD(self.token0.id, self.token1.id) / 100


class Pool:
    def __init__(self, token0_symbol:str, token1_symbol:str, fee_tier:int, context: 'ABCContext'):
        self.fee_tier: int = fee_tier
        self.context: 'ABCContext' = context
        self.token0: Token = Token(token0_symbol, self.context)
        self.token1: Token = Token(token1_symbol, self.context)

    @property
    def id(self):
        return self.context.pool_id(self.token0.id, self.token1.id, self.fee_tier)

    @property
    def tick(self):
        return self.context.pool_tick(self.token0.id, self.token1.id, self.fee_tier)

    @property
    def volumeUSD(self):
        return self.context.pool_volumeUSD(self.token0.id, self.token1.id, self.fee_tier) / 100

    @property
    def price0(self):
        return (1.0001 ** self.tick) * (10 ** self.token0.decimals) / (10 ** self.token1.decimals)

    @property
    def price1(self):
        return 1 / self.price0

    @property
    def tick_spacing(self):
        return self.context.tick_spacing(self.fee_tier)

    @property
    def ticks(self):
        return self.context.pool_ticks(self.id, self.fee_tier, self.token0.decimals, self.token1.decimals)

    @property
    def ohlc(self):
        return self.context.pool_ohlc(self.id)

    def plot_liquidity(self, min_x: float =0.9, max_x: float = 1.1, x: str = 'Price1'):
        bar_plot = self.ticks.copy()
        bar_plot.reset_index(inplace=True)
        bar_plot['color'] = np.where((bar_plot['tickIdx'] > self.tick) & (bar_plot['tickIdx'] < self.tick + self.tick_spacing), 'crimson', 'lightslategray')
        bar_plot['diff'] = (bar_plot['Price1']/self.price1)
        bar_plot = bar_plot[bar_plot['diff'].between(min_x, max_x)]
        bar_plot.sort_values(x, inplace=True)
        fig = px.bar(bar_plot, x=x, y='Liquidity', color='color')
        fig.show()

    def plot_ohlc(self):
        fig = go.Figure(data=go.Ohlc(x=self.ohlc.index, open=self.ohlc.open, high=self.ohlc.high, low=self.ohlc.low, close=self.ohlc.close))
        fig.show()

    def price_to_tick(self, price):
        return self.context.price_to_tick(price, self.token0.decimals, self.token1.decimals)

    def liquidity(self, amount0, amount1, currentprice, lowerprice, upperprice):
        amount0 = amount0 * 10**self.token0.decimals
        amount1 = amount1 * 10**self.token1.decimals

        upper = math.sqrt(upperprice * 10**self.token1.decimals / 10**self.token0.decimals) * 2**96
        lower = math.sqrt(lowerprice * 10**self.token1.decimals / 10**self.token0.decimals) * 2**96
        cprice = math.sqrt(currentprice * 10**self.token1.decimals / 10**self.token0.decimals) * 2**96

        if cprice <= lower:
            return amount0 * (upper * lower / 2**96) / (upper - lower)

        elif lower < cprice <= upper:
            liquidity0 = amount0 * (upper * cprice / 2**96) / (upper - cprice)
            liquidity1 = amount1 * 2**96 / (cprice - lower)
            return min(liquidity0, liquidity1)
        
        elif upper < cprice:
            return amount1 * 2**96 / (upper - lower)

    def tv(self, simulator, price, lowerprice, upperprice, amount0, amount1):
        print(self.token0.decimals, self.token1.decimals)
        print(amount0, amount1)
        ohlc = self.ohlc.iloc[-3*24:]

        average_hr_fees = self.volumeUSD * (self.fee_tier/1000000) / 24

        liquidity = self.liquidity(amount0, amount1, price, lowerprice, upperprice)
        tick_index = self.ticks.to_dict('index')

        simulator.sim(ohlc)
        simulator.line_graph()
        fees = []
        for col in simulator.simulations_dict:
            col_fees = []
            for node in simulator.simulations_dict[col]:
                tick = self.price_to_tick(node)
                closest_tick_spacing = tick - tick % self.tick_spacing
                tick_liquidity = tick_index[closest_tick_spacing]['Liquidity']
                average_fee_revenue = (liquidity/tick_liquidity) * average_hr_fees
                col_fees.append(average_fee_revenue)
            fees.append(col_fees)
        
        #print(fees)
        Ils = []
        for col in simulator.simulations_dict:
            last_price = simulator.simulations_dict[col][-1]
            
            upper = math.sqrt(upperprice * 10**self.token1.decimals / 10**self.token0.decimals) * 2**96
            lower = math.sqrt(lowerprice * 10**self.token1.decimals / 10**self.token0.decimals) * 2**96
            cprice = math.sqrt(1/last_price * 10**self.token1.decimals / 10**self.token0.decimals) * 2**96

            if cprice <= lower:
                amt0_lp = liquidity / (upper * lower / 2**96) * (upper - lower) / 10**self.token0.decimals
                amt1_lp = 0
            
            elif lower < cprice <= upper:
                amt0_lp = liquidity / (upper * cprice / 2**96) * (upper - cprice) / 10**self.token0.decimals
                amt1_lp = liquidity / 2**96 * (cprice - lower) / 10**self.token1.decimals
        
            elif upper < cprice:
                amt1_lp = liquidity / 2**96 * (upper - lower)/ 10**self.token1.decimals
                amt0_lp = 0

            print(price, 1/last_price, amt0_lp, amount0, amt1_lp, amount1)
            Ils.append((amt0_lp- amount0)*1/last_price +  amt1_lp - amount1)
        print(Ils)
        return sum([sum(fee) + Il for Il, fee in zip(Ils, fees)]) / len(simulator.simulations_dict) 


@dataclass
class LPUniswapV3:
    deposit_amount: float #always in USDC
    token0_symbol: str
    token1_symbol: str
    fee_tier:int
    context: ABCContext
    max_perc: float
    min_per: float

    def __post_init__(self):
        self.pool = Pool(self.token0_symbol, self.token1_symbol, self.fee_tier, self.context)
        self.amount0 = self.deposit_amount
        self.amount1 = self.get_amount1()
    
    @property
    def price_high(self):
        return self.pool.price0 * (1 + self.max_perc)
    
    @property
    def price_low(self):
        return self.pool.price0 * (1 - self.max_perc)

    def get_amount1(self):
        L = self.deposit_amount * math.sqrt(self.pool.price0) * math.sqrt(self.price_high) / (math.sqrt(self.price_high) - math.sqrt(self.pool.price0))
        return L * (math.sqrt(self.pool.price0) - math.sqrt(self.price_low))

    def get_amount0(self):
        L = self.deposit_amount / (math.sqrt(self.pool.price0) - math.sqrt(self.price_low))
        return L * (math.sqrt(self.price_high) - math.sqrt(self.pool.price0)) / (math.sqrt(self.pool.price0) * math.sqrt(self.price_high))

    def tv(self, simulator):
        print(self.pool.price0, self.price_low, self.price_high, self.amount0, self.amount1)
        return self.pool.tv(simulator, self.pool.price0, self.price_low, self.price_high, self.amount0, self.amount1)
