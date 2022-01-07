import asyncio

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport


async def query_gpl(query: str) -> dict:
    "Query a Client."
    counter = 1
    while True:
        async with Client(transport=AIOHTTPTransport(url="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"), fetch_schema_from_transport=True) as session:
            try:
                query_result = await session.execute(gql(query))
            except Exception as err:
                counter += 1
                if counter > 5:
                    raise Exception("Query GQL error") from err
                continue
            break
    return query_result


async def query_gql(querys: list[str]) -> list:
    "Perform multiple queries similtaniously."
    tasks = []
    for query in querys:
        tasks.append(query_gpl(query))
    responses = await asyncio.gather(*tasks)
    return responses


querys = [
    '{pool(id: "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"){poolDayData(first: 1000, skip: 0 orderBy: date orderDirection: desc where: {date_gte: 1641120978 date_lte: 1641578178}){date feesUSD volumeToken0 volumeToken1 volumeUSD}}}',
    '{pool(id: "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"){poolDayData(first: 1000, skip: 1000 orderBy: date orderDirection: desc where: {date_gte: 1641120978 date_lte: 1641578178}){date feesUSD volumeToken0 volumeToken1 volumeUSD}}}',
    '{pool(id: "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"){poolDayData(first: 1000, skip: 2000 orderBy: date orderDirection: desc where: {date_gte: 1641120978 date_lte: 1641578178}){date feesUSD volumeToken0 volumeToken1 volumeUSD}}}',
    '{pool(id: "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"){poolDayData(first: 1000, skip: 3000 orderBy: date orderDirection: desc where: {date_gte: 1641120978 date_lte: 1641578178}){date feesUSD volumeToken0 volumeToken1 volumeUSD}}}',
    '{pool(id: "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"){poolDayData(first: 1000, skip: 4000 orderBy: date orderDirection: desc where: {date_gte: 1641120978 date_lte: 1641578178}){date feesUSD volumeToken0 volumeToken1 volumeUSD}}}',
    '{pool(id: "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"){poolDayData(first: 1000, skip: 5000 orderBy: date orderDirection: desc where: {date_gte: 1641120978 date_lte: 1641578178}){date feesUSD volumeToken0 volumeToken1 volumeUSD}}}',
]


print(asyncio.get_event_loop().run_until_complete(query_gql(querys)))
