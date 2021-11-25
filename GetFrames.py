from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pandas as pd
pd.set_option('display.max_rows', None)

client = Client(
            transport=RequestsHTTPTransport(
            url='https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3',
            verify=True,
            retries=5))

token0Symbols = []
token1Symbols = []
feeTier = 0

def GetIDs(n, feeTier):
    print('\n\nGetting '+str(n)+' IDs with FeeTier: '+str(feeTier)+'...')
    if feeTier == 0:
        feeTier = ''

    else:
        feeTier= ', where: {feeTier: ' + str(feeTier) + '}'

    strGet = '{pools(first: '+str(n)+', orderBy:volumeUSD, orderDirection:desc'+str(feeTier)+') {id token0{symbol} token1{symbol}}}'

    idGet = client.execute(gql(strGet))
    poolIDs = []

    for i in range(0, n):
        poolIDs.append(idGet['pools'][i]['id'])
        token0Symbols.append(idGet['pools'][i]['token0']['symbol'])
        token1Symbols.append(idGet['pools'][i]['token1']['symbol'])

    return poolIDs

def GetFrames(poolIDs):
    print('\nGetting OHLC and Tick data for IDs...')

    dfList = []
    counter = 1
    a = 0


    for id in poolIDs:
        print('\n'+token0Symbols[a]+'/'+token1Symbols[a]+' poolID: ' + str(id))
        skip = 0
        ohlcList = []
        ticksList = []
        switch = True

        while switch == True:
            poolStr = '{pool(id: "'+id+'"){id feeTier liquidity sqrtPrice feeGrowthGlobal0X128 feeGrowthGlobal1X128 token0Price token1Price tick observationIndex volumeToken0 volumeToken1 volumeUSD untrackedVolumeUSD feesUSD txCount collectedFeesToken0 collectedFeesToken1 collectedFeesUSD liquidityProviderCount totalValueLockedUSD totalValueLockedETH totalValueLockedToken0 totalValueLockedToken1 token0{id symbol decimals}token1{id symbol decimals }poolHourData(first: 1000, skip: '+str(skip)+'){periodStartUnix close high low open}ticks(first: 1000, skip: '+str(skip)+'){tickIdx liquidityNet liquidityGross}}}'
            poolInfo = client.execute(gql(poolStr))

            for i in range(len(poolInfo['pool']['ticks'])):
                liqG = poolInfo['pool']['ticks'][i]['liquidityGross']
                liqN = poolInfo['pool']['ticks'][i]['liquidityNet']
                tickIdx = poolInfo['pool']['ticks'][i]['tickIdx']
                tempList = [liqG, liqN, tickIdx]
                ticksList.append(tempList)
            
            if len(poolInfo['pool']['ticks']) > 0:
                print(str(len(poolInfo['pool']['ticks'])) + ' Ticks added')

            for i in range(len(poolInfo['pool']['poolHourData'])):
                close = poolInfo['pool']['poolHourData'][i]['close']
                high = poolInfo['pool']['poolHourData'][i]['high']
                low = poolInfo['pool']['poolHourData'][i]['low']
                open = poolInfo['pool']['poolHourData'][i]['open']
                periodStartUnix = poolInfo['pool']['poolHourData'][i]['periodStartUnix']
                tempList = [close, high, low, open, periodStartUnix]
                ohlcList.append(tempList)

            if len(poolInfo['pool']['poolHourData']) > 0:
                print(str(len(poolInfo['pool']['poolHourData'])) + ' OHLC added')

            if skip == 5000:
                ohlcFrame = pd.DataFrame(ohlcList)
                ohlcFrame.columns = ['Close', 'High', 'Low', 'Open', 'psUnix']

                ticksFrame = pd.DataFrame(ticksList)
                ticksFrame.columns = ['liquidityGross', 'liquidityNet', 'tickIdx']

                sqrtPrice = poolInfo['pool']['sqrtPrice']
                liq = poolInfo['pool']['liquidity']
                feeTier = poolInfo['pool']['feeTier']
                t0id = poolInfo['pool']['token0']['id']
                t0symbol = poolInfo['pool']['token0']['symbol']
                t0decimals = poolInfo['pool']['token0']['decimals']
                t1id = poolInfo['pool']['token1']['id']
                t1symbol = poolInfo['pool']['token1']['symbol']
                t1decimals = poolInfo['pool']['token1']['decimals']
                feeGrowthGlobal0X128 = poolInfo['pool']['feeGrowthGlobal0X128']
                feeGrowthGlobal1X128 = poolInfo['pool']['feeGrowthGlobal1X128']
                token0Price = poolInfo['pool']['token0Price']
                token1Price = poolInfo['pool']['token1Price']
                tick = poolInfo['pool']['tick']
                observationIndex = poolInfo['pool']['observationIndex']
                volumeToken0 = poolInfo['pool']['volumeToken0']
                volumeToken1 = poolInfo['pool']['volumeToken1']
                volumeUSD = poolInfo['pool']['volumeUSD']
                untrackedVolumeUSD = poolInfo['pool']['untrackedVolumeUSD']
                feesUSD = poolInfo['pool']['feesUSD']
                txCount = poolInfo['pool']['txCount']
                collectedFeesToken0 = poolInfo['pool']['collectedFeesToken0']
                collectedFeesToken1 = poolInfo['pool']['collectedFeesToken1']
                collectedFeesUSD = poolInfo['pool']['collectedFeesUSD']
                liquidityProviderCount = poolInfo['pool']['liquidityProviderCount']
                totalValueLockedUSD = poolInfo['pool']['totalValueLockedUSD']
                totalValueLockedETH = poolInfo['pool']['totalValueLockedETH']
                totalValueLockedToken0 = poolInfo['pool']['totalValueLockedToken0']
                totalValueLockedToken1= poolInfo['pool']['totalValueLockedToken1']

                tempList = [id, liq, feeTier, sqrtPrice, t0id, t0symbol, t0decimals, t1id, t1symbol, t1decimals, feeGrowthGlobal0X128, feeGrowthGlobal1X128, token0Price, token1Price, tick, observationIndex, volumeToken0, volumeToken1, volumeUSD, untrackedVolumeUSD, feesUSD, txCount, collectedFeesToken0, collectedFeesToken1, collectedFeesUSD, liquidityProviderCount, totalValueLockedUSD, totalValueLockedETH, totalValueLockedToken0, totalValueLockedToken1, ohlcFrame, ticksFrame]
                dfList.append(tempList)

                print('\n' +str(round((counter / len(poolIDs))*100, 2)) + '% complete')
                counter+=1
                a += 1

                switch = False

            else:
                skip +=1000 

    print('\nGenerating DataFrame...\n')
    dfPools = pd.DataFrame(dfList)
    dfPools.columns = ['poolID', 'liquidity', 'FeeTier', 'sqrtPrice', 't0id', 't0symbol','t0decimals','t1id','t1symbol','t1decimals', 'feeGrowthGlobal0X128', 'feeGrowthGlobal1X128', 'token0Price', 'token1Price', 'tick', 'observationIndex', 'volumeToken0', 'volumeToken1', 'volumeUSD', 'untrackedVolumeUSD', 'feesUSD', 'txCount', 'collectedFeesToken0', 'collectedFeesToken1', 'collectedFeesUSD', 'liquidityProviderCount', 'totalValueLockedUSD', 'totalValueLockedETH', 'totalValueLockedToken0', 'totalValueLockedToken1','ohlcFrame', 'ticksFrame']
    print(dfPools)
    return dfPools

#GetIDs(n) takes n and returns a list of pool IDs, length n
#GetFrames(poolIDs) takes a list of pool IDs and returns a Dataframe for each
GetFrames(GetIDs(3, 3000))


