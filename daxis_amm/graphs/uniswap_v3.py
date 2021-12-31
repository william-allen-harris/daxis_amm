import logging
import multiprocessing
from urllib3 import disable_warnings

import pandas as pd
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

from daxis_amm.instruments.uniswap_v3 import Pool

client = Client(
    transport=RequestsHTTPTransport(
        url="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",  #'https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon',
        verify=True,
        retries=5,
    )
)


def query_gpl(query: str) -> dict:
    counter = 1
    while True:
        try:
            logging.info(f"Retreiving {query} for Subgraph")
            query_result = client.execute(gql(query))
        except Exception as e:
            logging.warning(f"Retrying(total={counter}. trying again... Error: {e}")
            counter += 1
            if counter > 5:
                logging.error(f"Query {query} failed 5 times... Stopping", exc_info=True)
                raise Exception("Query GQL error") from e
            continue
        break
    return query_result


def wrapper_query_gpl(query: str, return_dict: dict) -> None:
    return_dict[query] = query_gpl(query)


def query_multiple_gql(querys: list[str]) -> dict:
    manager = multiprocessing.Manager()
    return_dict = manager.dict()

    jobs = []
    for query in querys:
        p = multiprocessing.Process(target=wrapper_query_gpl, args=(query, return_dict))
        jobs.append(p)
        p.start()

    for proc in jobs:
        proc.join()
    return return_dict


def get_pool_info(pool_id):
    logging.info(f"Retreiving Pool {pool_id} Info for Subgraph")
    query = (
        '{pool(id: "'
        + pool_id
        + '"){id feeTier liquidity sqrtPrice feeGrowthGlobal0X128 feeGrowthGlobal1X128 token0Price token1Price tick observationIndex volumeToken0 volumeToken1 volumeUSD untrackedVolumeUSD feesUSD txCount collectedFeesToken0 collectedFeesToken1 collectedFeesUSD liquidityProviderCount totalValueLockedUSD totalValueLockedETH totalValueLockedToken0 totalValueLockedToken1 token0{id symbol decimals derivedETH}token1{id symbol decimals derivedETH}}bundles{ethPriceUSD}}'
    )
    result = query_gpl(query)
    sqrtPrice = result["pool"]["sqrtPrice"]
    liq = result["pool"]["liquidity"]
    feeTier = int(result["pool"]["feeTier"])
    t0id = result["pool"]["token0"]["id"]
    t0symbol = result["pool"]["token0"]["symbol"]
    t0decimals = int(result["pool"]["token0"]["decimals"])
    t0derivedETH = float(result["pool"]["token0"]["derivedETH"])
    t1id = result["pool"]["token1"]["id"]
    t1symbol = result["pool"]["token1"]["symbol"]
    t1decimals = int(result["pool"]["token1"]["decimals"])
    t1derivedETH = float(result["pool"]["token1"]["derivedETH"])
    feeGrowthGlobal0X128 = result["pool"]["feeGrowthGlobal0X128"]
    feeGrowthGlobal1X128 = result["pool"]["feeGrowthGlobal1X128"]
    token0Price = float(result["pool"]["token0Price"])
    token1Price = float(result["pool"]["token1Price"])
    tick = int(result["pool"]["tick"])
    observationIndex = result["pool"]["observationIndex"]
    volumeToken0 = result["pool"]["volumeToken0"]
    volumeToken1 = result["pool"]["volumeToken1"]
    volumeUSD = float(result["pool"]["volumeUSD"])
    untrackedVolumeUSD = result["pool"]["untrackedVolumeUSD"]
    feesUSD = float(result["pool"]["feesUSD"])
    txCount = result["pool"]["txCount"]
    collectedFeesToken0 = result["pool"]["collectedFeesToken0"]
    collectedFeesToken1 = result["pool"]["collectedFeesToken1"]
    collectedFeesUSD = result["pool"]["collectedFeesUSD"]
    liquidityProviderCount = result["pool"]["liquidityProviderCount"]
    totalValueLockedUSD = result["pool"]["totalValueLockedUSD"]
    totalValueLockedETH = result["pool"]["totalValueLockedETH"]
    totalValueLockedToken0 = result["pool"]["totalValueLockedToken0"]
    totalValueLockedToken1 = result["pool"]["totalValueLockedToken1"]
    ethPriceUSD = float(result["bundles"][0]["ethPriceUSD"])

    return [
        pool_id,
        liq,
        feeTier,
        sqrtPrice,
        t0id,
        t0symbol,
        t0decimals,
        t0derivedETH,
        t1id,
        t1symbol,
        t1decimals,
        t1derivedETH,
        feeGrowthGlobal0X128,
        feeGrowthGlobal1X128,
        token0Price,
        token1Price,
        tick,
        observationIndex,
        volumeToken0,
        volumeToken1,
        volumeUSD,
        untrackedVolumeUSD,
        feesUSD,
        txCount,
        collectedFeesToken0,
        collectedFeesToken1,
        collectedFeesUSD,
        liquidityProviderCount,
        totalValueLockedUSD,
        totalValueLockedETH,
        totalValueLockedToken0,
        totalValueLockedToken1,
        ethPriceUSD,
    ]


def get_pool_hour_data_info(pool_id):
    logging.info(f"Retreiving Pool Hour Data {pool_id} for Subgraph")

    querys = [
        (
            '{pool(id: "'
            + pool_id
            + '"){poolHourData(first: 1000, skip: '
            + str(skip)
            + "){periodStartUnix close high low open feesUSD}}}"
        )
        for skip in range(0, 6000, 1000)
    ]
    results = query_multiple_gql(querys)

    ohlc_hour_list = []
    for poolInfo in results.values():
        for i in range(len(poolInfo["pool"]["poolHourData"])):
            close = float(poolInfo["pool"]["poolHourData"][i]["close"])
            high = float(poolInfo["pool"]["poolHourData"][i]["high"])
            low = float(poolInfo["pool"]["poolHourData"][i]["low"])
            open = float(poolInfo["pool"]["poolHourData"][i]["open"])
            periodStartUnix = poolInfo["pool"]["poolHourData"][i]["periodStartUnix"]
            tempList = [close, high, low, open, periodStartUnix]
            ohlc_hour_list.append(tempList)
    return pd.DataFrame(ohlc_hour_list, columns=["Close", "High", "Low", "Open", "psUnix"])


def get_pool_day_data_info(pool_id):
    logging.info(f"Retreiving Pool Hour Day {pool_id} for Subgraph")

    querys = [
        ('{pool(id: "' + pool_id + '"){poolDayData(first: 1000, skip: ' + str(skip) + "){date feesUSD}}}")
        for skip in range(0, 6000, 1000)
    ]
    results = query_multiple_gql(querys)

    ohlc_day_list = []
    for poolInfo in results.values():
        for i in range(len(poolInfo["pool"]["poolDayData"])):
            fees_usd = float(poolInfo["pool"]["poolDayData"][i]["feesUSD"])
            date = float(poolInfo["pool"]["poolDayData"][i]["date"])
            tempList = [date, fees_usd]
            ohlc_day_list.append(tempList)
    return pd.DataFrame(ohlc_day_list, columns=["Date", "FeesUSD"])


def get_pool_ticks_info(pool_id):
    logging.info(f"Retreiving Pool Tick {pool_id} for Subgraph")

    querys = [
        ('{pool(id: "' + pool_id + '"){ticks(first: 1000, skip: ' + str(skip) + "){tickIdx liquidityNet liquidityGross}}}")
        for skip in range(0, 6000, 1000)
    ]
    results = query_multiple_gql(querys)

    ticks_list = []
    for poolInfo in results.values():
        for i in range(len(poolInfo["pool"]["ticks"])):
            liqG = float(poolInfo["pool"]["ticks"][i]["liquidityGross"])
            liqN = float(poolInfo["pool"]["ticks"][i]["liquidityNet"])
            tickIdx = int(poolInfo["pool"]["ticks"][i]["tickIdx"])
            ticks_list.append([liqG, liqN, tickIdx])
    return pd.DataFrame(ticks_list, columns=["liquidityGross", "liquidityNet", "tickIdx"])


def get_pool(pool_id: str) -> Pool:
    logging.info(f"Building Pool class {pool_id} from Subgraph")

    return Pool(
        *get_pool_info(pool_id),
        OHLC_df=get_pool_hour_data_info(pool_id),
        OHLC_day_df=get_pool_day_data_info(pool_id),
        Ticks_df=get_pool_ticks_info(pool_id),
    )
