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
def GetIDs(n):
    print('\n\nGetting IDs...')

    strGet = '{pools(first: '+str(n)+', orderBy:volumeUSD, orderDirection:desc) {id token0{symbol} token1{symbol}}}'
    idGet = client.execute(gql(strGet))
    poolIDs = []
    finalList = []

    for i in range(0, n):
        poolIDs.append(idGet['pools'][i]['id'])
        token0Symbols.append(idGet['pools'][i]['token0']['symbol'])
        token1Symbols.append(idGet['pools'][i]['token1']['symbol'])

    print('Done')

    return poolIDs

def GetFrames(poolIDs):
    print('\nGetting OHLC and Tick data for IDs...')

    dfList = []
    counter = 1

    for id in poolIDs:
        a = 0
        print('\n'+token0Symbols[a]+'/'+token1Symbols[a]+' poolID: ' + str(id))
        a += 1
        skip = 0
        ohlcList = []
        ticksList = []
        switch = True

        while switch == True:
            poolStr = '{pool(id: "'+id+'"){id token0{symbol}token1{symbol}poolHourData(first: 1000, skip: '+str(skip)+'){periodStartUnix close high low open}ticks(first: 1000, skip: '+str(skip)+'){tickIdx liquidityNet liquidityGross}}}'
            poolInfo = client.execute(gql(poolStr))

            if len(poolInfo['pool']['poolHourData']) > 0:
                print(str(len(poolInfo['pool']['poolHourData'])) + ' OHLC added')

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

            for i in range(len(poolInfo['pool']['ticks'])):
                liqG = poolInfo['pool']['ticks'][i]['liquidityGross']
                liqN = poolInfo['pool']['ticks'][i]['liquidityNet']
                tickIdx = poolInfo['pool']['ticks'][i]['tickIdx']
                tempList = [liqG, liqN, tickIdx]
                ticksList.append(tempList)

            if skip == 5000:
                ohlcFrame = pd.DataFrame(ohlcList)
                ohlcFrame.columns = ['Close', 'High', 'Low', 'Open', 'psUnix']
                ticksFrame = pd.DataFrame(ticksList)
                ticksFrame.columns = ['liquidityGross', 'liquidityNet', 'tickIdx']
                tempList = [id, ohlcFrame, ticksFrame]
                dfList.append(tempList)

                print('\n' +str(round((counter / len(poolIDs))*100, 2)) + '% complete')
                counter+=1
                switch = False

            else:
                skip +=1000 

    print('\nGenerating DataFrame...\n')
    dfPools = pd.DataFrame(dfList)
    dfPools.columns = ['poolID', 'ohlcFrame', 'ticksFrame']
    print(dfPools)
    return dfPools

#GetIDs(n) takes n and returns a list of pool IDs, length n
#GetFrames(poolIDs) takes a list of pool IDs and returns a Dataframe for each
GetFrames(GetIDs(7))
