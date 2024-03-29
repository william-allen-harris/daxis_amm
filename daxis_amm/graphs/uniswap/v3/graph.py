"""
Module defining the Uniswap V3 Graphs.
"""
import logging as _log

import pandas as _pd

from daxis_amm.instruments.uniswap_v3 import Pool, Token
from daxis_amm.graphs.base import BaseGraph


class UniswapV3Graph(BaseGraph):
    """
    Class defining Uniswap V3 Graphs.
    """

    url: str = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"

    @classmethod
    async def get_static_pool_info(cls, pool_id: str):
        """
        Get static pool information from the Subgraph.

        :param pool_id: The ID of the pool.
        :type pool_id: str
        :return: The static pool information.
        :rtype: dict
        """
        _log.info(f"Retrieving Pool {pool_id} Static Info for Subgraph")
        query = [
            (
                '{pool(id: "'
                + pool_id
                + '"){id feeTier token0{id symbol name decimals totalSupply}token1{id symbol name decimals totalSupply}}}'
            )
        ]
        results = await cls.query_gql(query)
        return results[0]

    @classmethod
    async def get_dynamic_pool_info(cls, pool_id: str):
        """
        Get dynamic pool information from the Subgraph.

        :param pool_id: The ID of the pool.
        :type pool_id: str
        :return: The dynamic pool information.
        :rtype: dict
        """
        _log.info(f"Retrieving Pool {pool_id} Info for Subgraph")
        query = [
            (
                '{pool(id: "'
                + pool_id
                + '"){id feeTier liquidity sqrtPrice feeGrowthGlobal0X128 feeGrowthGlobal1X128 token0Price token1Price tick observationIndex volumeToken0 volumeToken1 volumeUSD untrackedVolumeUSD feesUSD txCount collectedFeesToken0 collectedFeesToken1 collectedFeesUSD liquidityProviderCount totalValueLockedUSD totalValueLockedETH totalValueLockedToken0 totalValueLockedToken1 token0{id symbol decimals derivedETH}token1{id symbol decimals derivedETH}}bundles{ethPriceUSD}}'
            )
        ]
        results = await cls.query_gql(query)
        result = results[0]
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

        return {
            "pool_id": pool_id,
            "liq": liq,
            "feeTier": feeTier,
            "sqrtPrice": sqrtPrice,
            "t0id": t0id,
            "t0symbol": t0symbol,
            "t0decimals": t0decimals,
            "t0derivedETH": t0derivedETH,
            "t1id": t1id,
            "t1symbol": t1symbol,
            "t1decimals": t1decimals,
            "t1derivedETH": t1derivedETH,
            "feeGrowthGlobal0X128": feeGrowthGlobal0X128,
            "feeGrowthGlobal1X128": feeGrowthGlobal1X128,
            "token0Price": token0Price,
            "token1Price": token1Price,
            "tick": tick,
            "observationIndex": observationIndex,
            "volumeToken0": volumeToken0,
            "volumeToken1": volumeToken1,
            "volumeUSD": volumeUSD,
            "untrackedVolumeUSD": untrackedVolumeUSD,
            "feesUSD": feesUSD,
            "txCount": txCount,
            "collectedFeesToken0": collectedFeesToken0,
            "collectedFeesToken1": collectedFeesToken1,
            "collectedFeesUSD": collectedFeesUSD,
            "liquidityProviderCount": liquidityProviderCount,
            "totalValueLockedUSD": totalValueLockedUSD,
            "totalValueLockedETH": totalValueLockedETH,
            "totalValueLockedToken0": totalValueLockedToken0,
            "totalValueLockedToken1": totalValueLockedToken1,
            "ethPriceUSD": ethPriceUSD,
        }

    @classmethod
    async def get_token_day_data_info(cls, token_id: str):
        """
        Get token day data from the Subgraph.

        :param token_id: The ID of the token.
        :type token_id: str
        :return: The token day data.
        :rtype: pd.DataFrame
        """
        _log.info(f"Retrieving Token Day Data {token_id} for Subgraph")

        querys = [
            (
                '{token(id: "'
                + token_id
                + '"){tokenDayData(first: 1000, skip: '
                + str(skip)
                + " orderBy: date orderDirection: desc){date close high low open}}}"
            )
            for skip in range(0, 6000, 1000)
        ]
        results = await cls.query_gql(querys)

        ohlc_hour_list = []
        for poolInfo in results:
            for i in range(len(poolInfo["token"]["tokenDayData"])):
                close = float(poolInfo["token"]["tokenDayData"][i]["close"])
                high = float(poolInfo["token"]["tokenDayData"][i]["high"])
                low = float(poolInfo["token"]["tokenDayData"][i]["low"])
                open = float(poolInfo["token"]["tokenDayData"][i]["open"])
                date = poolInfo["token"]["tokenDayData"][i]["date"]
                tempList = [close, high, low, open, date]
                ohlc_hour_list.append(tempList)
        return _pd.DataFrame(ohlc_hour_list, columns=["Close", "High", "Low", "Open", "Date"])

    @classmethod
    async def get_token_hour_data_info(cls, token_id: str, start_date, end_date):
        """
        Get token hour data from the Subgraph.

        :param token_id: The ID of the token.
        :type token_id: str
        :param start_date: The start date for the data.
        :param end_date: The end date for the data.
        :return: The token hour data.
        :rtype: pd.DataFrame
        """
        _log.info(f"Retrieving Token Hour Data {token_id} for Subgraph")

        querys = [
            (
                "{tokenHourDatas(first: 1000 skip:"
                + str(skip)
                + ' orderBy:periodStartUnix orderDirection:desc where: {token:"'
                + str(token_id)
                + '" periodStartUnix_gte: '
                + str(start_date)
                + " periodStartUnix_lte: "
                + str(end_date)
                + "}){periodStartUnix close open high low}}"
            )
            for skip in range(0, 6000, 1000)
        ]
        results = await cls.query_gql(querys)

        ohlc_hour_list = []
        for poolInfo in results:
            for i in range(len(poolInfo["tokenHourDatas"])):
                close = float(poolInfo["tokenHourDatas"][i]["close"])
                high = float(poolInfo["tokenHourDatas"][i]["high"])
                low = float(poolInfo["tokenHourDatas"][i]["low"])
                open = float(poolInfo["tokenHourDatas"][i]["open"])
                periodStartUnix = poolInfo["tokenHourDatas"][i]["periodStartUnix"]
                tempList = [close, high, low, open, periodStartUnix]
                ohlc_hour_list.append(tempList)
        return _pd.DataFrame(ohlc_hour_list, columns=["Close", "High", "Low", "Open", "psUnix"]).sort_values("psUnix")

    @classmethod
    async def get_pool_hour_data_info(cls, pool_id: str, start_date, end_date):
        """
        Get pool hour data from the Subgraph.

        :param pool_id: The ID of the pool.
        :type pool_id: str
        :param start_date: The start date for the data.
        :param end_date: The end date for the data.
        :return: The pool hour data.
        :rtype: pd.DataFrame
        """
        _log.info(f"Retrieving Pool Hour Data {pool_id} for Subgraph")

        querys = [
            (
                '{pool(id: "'
                + pool_id
                + '"){poolHourData(first: 1000, skip: '
                + str(skip)
                + " orderBy: periodStartUnix orderDirection: desc where: {periodStartUnix_gte: "
                + str(start_date)
                + " periodStartUnix_lte: "
                + str(end_date)
                + "}){periodStartUnix close high low open feesUSD}}}"
            )
            for skip in range(0, 6000, 1000)
        ]

        results = await cls.query_gql(querys)

        ohlc_hour_list = []
        for poolInfo in results:
            for i in range(len(poolInfo["pool"]["poolHourData"])):
                close = float(poolInfo["pool"]["poolHourData"][i]["close"])
                high = float(poolInfo["pool"]["poolHourData"][i]["high"])
                low = float(poolInfo["pool"]["poolHourData"][i]["low"])
                open = float(poolInfo["pool"]["poolHourData"][i]["open"])
                fees_usd = float(poolInfo["pool"]["poolHourData"][i]["feesUSD"])
                periodStartUnix = poolInfo["pool"]["poolHourData"][i]["periodStartUnix"]
                tempList = [close, high, low, open, fees_usd, periodStartUnix]
                ohlc_hour_list.append(tempList)
        return _pd.DataFrame(ohlc_hour_list, columns=["Close", "High", "Low", "Open", "feesUSD", "psUnix"]).sort_values("psUnix")

    @classmethod
    async def get_pool_day_data_info(cls, pool_id: str, start_date, end_date):
        """
        Get pool day data from the Subgraph.

        :param pool_id: The ID of the pool.
        :type pool_id: str
        :param start_date: The start date for the data.
        :param end_date: The end date for the data.
        :return: The pool day data.
        :rtype: pd.DataFrame
        """
        _log.info(f"Retrieving Pool Hour Day {pool_id} for Subgraph")

        querys = [
            (
                '{pool(id: "'
                + pool_id
                + '"){poolDayData(first: 1000, skip: '
                + str(skip)
                + " orderBy: date orderDirection: desc where: {date_gte: "
                + str(start_date)
                + " date_lte: "
                + str(end_date)
                + "}){date feesUSD volumeToken0 volumeToken1 volumeUSD}}}"
            )
            for skip in range(0, 6000, 1000)
        ]
        results = await cls.query_gql(querys)

        ohlc_day_list = []
        for poolInfo in results:
            for i in range(len(poolInfo["pool"]["poolDayData"])):
                fees_usd = float(poolInfo["pool"]["poolDayData"][i]["feesUSD"])
                volume_token0 = float(poolInfo["pool"]["poolDayData"][i]["volumeToken0"])
                volume_token1 = float(poolInfo["pool"]["poolDayData"][i]["volumeToken1"])
                volume_usd = float(poolInfo["pool"]["poolDayData"][i]["volumeUSD"])
                date = float(poolInfo["pool"]["poolDayData"][i]["date"])
                tempList = [date, fees_usd, volume_token0, volume_token1, volume_usd]
                ohlc_day_list.append(tempList)
        return _pd.DataFrame(ohlc_day_list, columns=["Date", "FeesUSD", "volumeToken0", "volumeToken1", "volumeUSD"])

    @classmethod
    async def get_pool_ticks_info(cls, pool_id: str):
        """
        Get pool ticks information from the Subgraph.

        :param pool_id: The ID of the pool.
        :type pool_id: str
        :return: The pool ticks information.
        :rtype: pd.DataFrame
        """
        _log.info(f"Retrieving Pool Tick {pool_id} for Subgraph")

        querys = [
            ('{pool(id: "' + pool_id + '"){ticks(first: 1000, skip: ' + str(skip) + "){tickIdx liquidityNet liquidityGross}}}")
            for skip in range(0, 6000, 1000)
        ]
        results = await cls.query_gql(querys)

        ticks_list = []
        for poolInfo in results:
            for i in range(len(poolInfo["pool"]["ticks"])):
                liqG = float(poolInfo["pool"]["ticks"][i]["liquidityGross"])
                liqN = float(poolInfo["pool"]["ticks"][i]["liquidityNet"])
                tickIdx = int(poolInfo["pool"]["ticks"][i]["tickIdx"])
                ticks_list.append([liqG, liqN, tickIdx])
        return _pd.DataFrame(ticks_list, columns=["liquidityGross", "liquidityNet", "tickIdx"]).sort_values("tickIdx")

    @classmethod
    async def get_pool_ticks_day_data_info(cls, pool_id: str, date):
        """
        Get pool tick day data from the Subgraph.

        :param pool_id: The ID of the pool.
        :type pool_id: str
        :param date: The date for the data.
        :return: The pool tick day data.
        :rtype: pd.DataFrame
        """
        _log.info(f"Retrieving Pool Tick Day Data {pool_id} for Subgraph")

        querys = [
            "{tickDayDatas(first: 1000, skip: "
            + str(skip)
            + 'where: {pool: "'
            + pool_id
            + '" date: '
            + str(date)
            + "}){tick {tickIdx} liquidityNet liquidityGross}}"
            for skip in range(0, 6000, 1000)
        ]

        results = await cls.query_gql(querys)

        ticks_list = []
        for poolInfo in results:
            for i in range(len(poolInfo["tickDayDatas"])):
                liqG = float(poolInfo["tickDayDatas"][i]["liquidityGross"])
                liqN = float(poolInfo["tickDayDatas"][i]["liquidityNet"])
                tickIdx = int(poolInfo["tickDayDatas"][i]["tick"]["tickIdx"])
                ticks_list.append([liqG, liqN, tickIdx])
        return _pd.DataFrame(ticks_list, columns=["liquidityGross", "liquidityNet", "tickIdx"]).sort_values("tickIdx")


def get_pool(pool_id: str) -> Pool:
    """
    Build a Pool class from a pool_id.

    :param pool_id: The ID of the pool.
    :type pool_id: str
    :return: The Pool class.
    :rtype: Pool
    """
    _log.info(f"Building Pool class {pool_id} from Subgraph")
    info = UniswapV3Graph.run({"pool_info": UniswapV3Graph.get_static_pool_info(pool_id)})

    fee_tier = int(info["pool_info"]["pool"]["feeTier"])
    pool_id = str(info["pool_info"]["pool"]["id"])

    token_0 = Token(
        id=str(info["pool_info"]["pool"]["token0"]["id"]),
        decimals=int(info["pool_info"]["pool"]["token0"]["decimals"]),
        symbol=str(info["pool_info"]["pool"]["token0"]["symbol"]),
        total_supply=int(info["pool_info"]["pool"]["token0"]["totalSupply"]),
        name=str(info["pool_info"]["pool"]["token0"]["name"]),
    )

    token_1 = Token(
        id=str(info["pool_info"]["pool"]["token1"]["id"]),
        decimals=int(info["pool_info"]["pool"]["token1"]["decimals"]),
        symbol=str(info["pool_info"]["pool"]["token1"]["symbol"]),
        total_supply=int(info["pool_info"]["pool"]["token1"]["totalSupply"]),
        name=str(info["pool_info"]["pool"]["token1"]["name"]),
    )
    return Pool(id=pool_id, fee_tier=fee_tier, token_0=token_0, token_1=token_1)
