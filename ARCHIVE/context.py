
from dataclasses import dataclass, field
from base_token import ABCContext
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import math

import pandas as pd


OPTIMISIM = 'https://api.thegraph.com/subgraphs/name/proy24/uniswap-optimism-subgraph'
UNISWAP_V3 = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
ARBITRUM = 'https://api.thegraph.com/subgraphs/name/ianlapham/arbitrum-minimal'
TRADERJOE = 'https://api.thegraph.com/subgraphs/name/traderjoe-xyz/exchange'


@dataclass
class TraderJoeClient(ABCContext):
    client: Client = Client(
            transport=RequestsHTTPTransport(
            url=TRADERJOE,
            verify=True,
            retries=5)
        )
    tokens: dict = field(default_factory=dict)

    def _get_token_info(self, symbol: str) -> dict:
        query = gql('{tokens(where: {symbol: "%s"}){name id symbol decimals}}' % symbol)
        self.tokens.update({symbol: self.client.execute(query)})

    def token_id(self, symbol) -> dict:
        if symbol not in self.tokens:
            self._get_token_info(symbol)
        
        return self.tokens[symbol]['tokens'][0]['id']

    def token_name(self, symbol) -> dict:
        if symbol not in self.tokens:
            self._get_token_info(symbol)

        return self.tokens[symbol]['tokens'][0]['name']

    def token_decimals(self, symbol):
        if symbol not in self.tokens:
            self._get_token_info(symbol)

        return int(self.tokens[symbol]['tokens'][0]['decimals'])

    def _get_pool_info(self, token0_id, token1_id):
        query = gql('{pairs(where: {token0: "%s" token1: "%s"}){id volumeUSD}}' % (token0_id, token1_id))
        return self.client.execute(query)

    def pool_id(self, token0_id, token1_id):
        return self._get_pool_info(token0_id, token1_id)['pairs'][0]['id']

    def pool_volumeUSD(self, token0_id, token1_id):
        return float(self._get_pool_info(token0_id, token1_id)['pairs'][0]['volumeUSD'])

@dataclass
class UniswapV3Client(ABCContext):
    client: Client = Client(
            transport=RequestsHTTPTransport(
            url=UNISWAP_V3,
            verify=True,
            retries=5)
        )
    tokens: dict = field(default_factory=dict)

    def tick_spacing(self, fee_tier):
        return {10000: 200, 3000: 60, 500: 10}[fee_tier]

    def _get_token_info(self, symbol: str) -> dict:
        query = gql('{tokens(where: {symbol: "%s"}){name id symbol decimals}}' % symbol)
        self.tokens.update({symbol: self.client.execute(query)})

    def _get_pool_info(self, token0_id, token1_id, fee_tier):
        query = gql('{pools(where: {token0: "%s" token1: "%s" feeTier: %s}){id tick volumeUSD}}' % (token0_id, token1_id, fee_tier))
        return self.client.execute(query)

    def _get_pool_ticks(self, pool_id, fee_tier, decimals0, decimals1):
        results = []
        for skip in range(0, 5):
            current_skip = skip * 1000
            query = gql('{pool(id: "%s"){ticks(first: 1000, skip: %s){tickIdx liquidityNet liquidityGross}}}' % (pool_id, current_skip))
            current_info = self.client.execute(query)
            if len(current_info['pool']['ticks']) > 0:
                results.extend(current_info['pool']['ticks'])
            else:
                break
        print('{pool(id: "%s"){ticks(first: 1000, skip: %s){tickIdx liquidityNet liquidityGross}}}' % (pool_id, current_skip))
        for i in range(len(results)):
            if i == 0:
                results[i]['liquidity'] = int(results[i]['liquidityGross'])
            else:
                results[i]['liquidity'] = results[i-1]['liquidity'] - int(results[i]['liquidityNet'])

        tick_index = {int(tick['tickIdx']): int(tick['liquidity']) for tick in results}
        tick_list = []
        for tick in range(min(tick_index), max(tick_index), self.tick_spacing(fee_tier)):
            prices = self.tick_to_price(tick, decimals0, decimals1)
            liquidity = tick_index[tick] if tick in tick_index else tick_list[-1][3]
            tick_list.append([tick, prices['token0_price'], prices['token1_price'], liquidity])
        
        df = pd.DataFrame(tick_list, columns=['tickIdx', 'Price0', 'Price1', 'Liquidity'])
        df.set_index('tickIdx', inplace=True)
        return df

    def _get_pool_hour_data(self, pool_id):
        results = []
        for skip in range(0, 5):
            current_skip = skip * 1000
            query = gql('{pool(id: "%s" orderDirection: desc){poolHourData(first: 1000, skip: %s){periodStartUnix close high low open}}}' % (pool_id, current_skip))
            current_info = self.client.execute(query)
            if len(current_info['pool']['poolHourData']) > 0:
                results.extend([c for c in current_info['pool']['poolHourData'] if '0' not in c.values()])
            else:
                break

        df = pd.DataFrame(results)
        df['Close'] = pd.to_numeric(df['close'])
        df['datetime'] = pd.to_datetime(df['periodStartUnix'], unit='s')
        df.set_index('datetime', inplace=True)

        return df
    
    def token_id(self, symbol) -> dict:
        if symbol not in self.tokens:
            self._get_token_info(symbol)
        
        return self.tokens[symbol]['tokens'][0]['id']

    def token_name(self, symbol) -> dict:
        if symbol not in self.tokens:
            self._get_token_info(symbol)

        return self.tokens[symbol]['tokens'][0]['name']

    def token_decimals(self, symbol):
        if symbol not in self.tokens:
            self._get_token_info(symbol)

        return int(self.tokens[symbol]['tokens'][0]['decimals'])

    def pool_id(self, token0_id, token1_id, fee_tier):
        return self._get_pool_info(token0_id, token1_id, fee_tier)['pools'][0]['id']

    def pool_tick(self, token0_id, token1_id, fee_tier):
        print(self._get_pool_info(token0_id, token1_id, fee_tier))
        return int(self._get_pool_info(token0_id, token1_id, fee_tier)['pools'][0]['tick'])

    def pool_volumeUSD(self, token0_id, token1_id, fee_tier):
        return float(self._get_pool_info(token0_id, token1_id, fee_tier)['pools'][0]['volumeUSD'])

    def pool_ticks(self, pool_id, fee_tier, decimals0, decimals1):
        return self._get_pool_ticks(pool_id, fee_tier, decimals0, decimals1)

    def pool_ohlc(self, pool_id):
        return self._get_pool_hour_data(pool_id)

    def tick_to_price(self, tick: str, decimals0, decimals1) -> dict:
        token0_price =  1.0001**(int(tick)) * (10**decimals0) / (10**decimals1)
        return {'token0_price': token0_price, 'token1_price': 1/token0_price}

    def price_to_tick(self, price: int, decimals0, decimals1) -> dict:
        return math.floor(math.log(1/price * (10**decimals1) / (10**decimals0)) / math.log(1.0001))

@dataclass
class UniswapV3OptimismClient(UniswapV3Client):
    client: Client = Client(
            transport=RequestsHTTPTransport(
            url=OPTIMISIM,
            verify=True,
            retries=5)
        )

@dataclass
class UniswapV3ArbitrumClient(UniswapV3Client):
    client: Client = Client(
            transport=RequestsHTTPTransport(
            url=ARBITRUM,
            verify=True,
            retries=5)
        )
