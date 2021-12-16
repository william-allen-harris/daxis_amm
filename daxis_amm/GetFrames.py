from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pandas as pd
import matplotlib.pyplot as plt
import os.path
from daxis_amm.pool import Pool
#pd.set_option('display.max_rows', None)

client = Client(
    transport=RequestsHTTPTransport(
        url='https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3',
        verify=True,
        retries=5))

token0Symbols = []
token1Symbols = []
ohlcFrames = []
ticksFrames = []
poolIDs = []
feeTier = 0


def GetIDs(n, feeTier):
    # GetIDs(n, FeeTier) returns a list of pool IDs
    # n: length of list
    # FeeTier: Sort by FeeTier (use 0 for no sorting)
    if feeTier == 0:
        print('\n\nGetting '+str(n)+' IDs - no FeeTier requirement...')
        feeTier = ''

    else:
        print('\n\nGetting '+str(n)+' IDs with FeeTier: '+str(feeTier)+'...')
        feeTier = ', where: {feeTier: ' + str(feeTier) + '}'

    strGet = '{pools(first: '+str(n)+', orderBy:volumeUSD, orderDirection:desc'+str(feeTier)+') {id token0{symbol} token1{symbol}}}'
    while True:
        try:
            idGet = client.execute(gql(strGet))
        except Exception as e:
            print(e)
            print('Error. trying again...')
            continue
        break
    global poolIDs
    print(len(idGet['pools']))
    for i in range(0, len(idGet['pools'])):
        poolIDs.append(idGet['pools'][i]['id'])
        token0Symbols.append(idGet['pools'][i]['token0']['symbol'])
        token1Symbols.append(idGet['pools'][i]['token1']['symbol'])

    return poolIDs


def GetFrames(poolIDs, return_type='DataFrame'):
    # GetFrames(poolIDs) returns a Dataframe of pools
    # poolIDs: list of poolIDs
    print('\nGetting OHLC and Tick data for IDs...')

    dfList = []
    counter = 1
    a = 0

    for id in poolIDs:
        print('\n'+token0Symbols[a]+'/'+token1Symbols[a]+' poolID: ' + str(id))
        skip = 0
        ohlcList = []
        ticksList = []

        while True:
            poolStr = '{pool(id: "'+id+'"){id feeTier liquidity sqrtPrice feeGrowthGlobal0X128 feeGrowthGlobal1X128 token0Price token1Price tick observationIndex volumeToken0 volumeToken1 volumeUSD untrackedVolumeUSD feesUSD txCount collectedFeesToken0 collectedFeesToken1 collectedFeesUSD liquidityProviderCount totalValueLockedUSD totalValueLockedETH totalValueLockedToken0 totalValueLockedToken1 token0{id symbol decimals}token1{id symbol decimals }poolHourData(first: 1000, skip: '+str(
                skip)+'){periodStartUnix close high low open}ticks(first: 1000, skip: '+str(skip)+'){tickIdx liquidityNet liquidityGross}}}'

            while True:
                try:
                    poolInfo = client.execute(gql(poolStr))
                except Exception as e:
                    print(e)
                    print('Error. trying again...')
                    continue
                break

            for i in range(len(poolInfo['pool']['ticks'])):
                liqG = float(poolInfo['pool']['ticks'][i]['liquidityGross'])
                liqN = float(poolInfo['pool']['ticks'][i]['liquidityNet'])
                tickIdx = int(poolInfo['pool']['ticks'][i]['tickIdx'])
                tempList = [liqG, liqN, tickIdx]
                ticksList.append(tempList)

            if len(poolInfo['pool']['ticks']) > 0:
                print(str(len(poolInfo['pool']['ticks'])) + ' Ticks added')

            for i in range(len(poolInfo['pool']['poolHourData'])):
                close = float(poolInfo['pool']['poolHourData'][i]['close'])
                high = float(poolInfo['pool']['poolHourData'][i]['high'])
                low = float(poolInfo['pool']['poolHourData'][i]['low'])
                open = float(poolInfo['pool']['poolHourData'][i]['open'])
                periodStartUnix = poolInfo['pool']['poolHourData'][i]['periodStartUnix']
                tempList = [close, high, low, open, periodStartUnix]
                ohlcList.append(tempList)

            if len(poolInfo['pool']['poolHourData']) > 0:
                print(str(len(poolInfo['pool']['poolHourData'])) + ' OHLC added')

            if skip == 5000:
                ohlcFrame = pd.DataFrame(ohlcList)
                ohlcFrame.columns = ['Close', 'High', 'Low', 'Open', 'psUnix']
                ohlcFrames.append(ohlcFrame)

                ticksFrame = pd.DataFrame(ticksList)
                ticksFrame.columns = ['liquidityGross', 'liquidityNet', 'tickIdx']
                ticksFrames.append(ticksFrame)

                sqrtPrice = poolInfo['pool']['sqrtPrice']
                liq = poolInfo['pool']['liquidity']
                feeTier = int(poolInfo['pool']['feeTier'])
                t0id = poolInfo['pool']['token0']['id']
                t0symbol = poolInfo['pool']['token0']['symbol']
                t0decimals = int(poolInfo['pool']['token0']['decimals'])
                t1id = poolInfo['pool']['token1']['id']
                t1symbol = poolInfo['pool']['token1']['symbol']
                t1decimals = int(poolInfo['pool']['token1']['decimals'])
                feeGrowthGlobal0X128 = poolInfo['pool']['feeGrowthGlobal0X128']
                feeGrowthGlobal1X128 = poolInfo['pool']['feeGrowthGlobal1X128']
                token0Price = float(poolInfo['pool']['token0Price'])
                token1Price = float(poolInfo['pool']['token1Price'])
                tick = int(poolInfo['pool']['tick'])
                observationIndex = poolInfo['pool']['observationIndex']
                volumeToken0 = poolInfo['pool']['volumeToken0']
                volumeToken1 = poolInfo['pool']['volumeToken1']
                volumeUSD = float(poolInfo['pool']['volumeUSD'])
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
                totalValueLockedToken1 = poolInfo['pool']['totalValueLockedToken1']

                tempList = [
                    id, liq, feeTier, sqrtPrice, t0id, t0symbol, t0decimals, t1id, t1symbol, t1decimals,
                    feeGrowthGlobal0X128, feeGrowthGlobal1X128, token0Price, token1Price, tick, observationIndex,
                    volumeToken0, volumeToken1, volumeUSD, untrackedVolumeUSD, feesUSD, txCount, collectedFeesToken0,
                    collectedFeesToken1, collectedFeesUSD, liquidityProviderCount, totalValueLockedUSD,
                    totalValueLockedETH, totalValueLockedToken0, totalValueLockedToken1, ohlcFrame, ticksFrame]
                dfList.append(tempList)

                print('\n' + str(round((counter / len(poolIDs))*100, 2)) + '% complete')
                counter += 1
                a += 1
                break

            else:
                skip += 1000

    global dfPools
    if return_type == 'DataFrame':
        print('\nGenerating DataFrame...')

        dfPools = pd.DataFrame(dfList)
        dfPools.columns = [
            'poolID', 'liquidity', 'FeeTier', 'sqrtPrice', 't0id', 't0symbol', 't0decimals', 't1id', 't1symbol',
            't1decimals', 'feeGrowthGlobal0X128', 'feeGrowthGlobal1X128', 'token0Price', 'token1Price', 'tick',
            'observationIndex', 'volumeToken0', 'volumeToken1', 'volumeUSD', 'untrackedVolumeUSD', 'feesUSD', 'txCount',
            'collectedFeesToken0', 'collectedFeesToken1', 'collectedFeesUSD', 'liquidityProviderCount',
            'totalValueLockedUSD', 'totalValueLockedETH', 'totalValueLockedToken0', 'totalValueLockedToken1', 'OHLC_df',
            'Ticks_df']
        print('Done!')
        return dfPools

    if return_type == 'Object':
        print('\nGenerating Pool Objects...')
        return [Pool(*pool_info) for pool_info in dfList]


def testPrint():
    # ohlcFrames
    # ticksFrames
    # these lists store the dataframes of ohlc and ticks (DataFrame within DataFrame ended up breaking the data)
    # they are indexed the same as dfPools, so
    # the pool at 0 index in dfPools will have its ohlc and ticks in ohlcFrames[0] and ticksFrames[0]
    GetFrames(GetIDs(1, 3000))
    print('\nExample output for one pool...')
    print('\nEntry into "list of pools" DataFrame:')
    print(dfPools.loc[[0]])
    print('\nOHLC DataFrame:')
    print(ohlcFrames[0])
    print('\nTicks DataFrame:')
    print(ticksFrames[0])


def testCSV():
    # take 2 coins and try to save their things
    # output as CSV to get a better visual idea of the data structure
    GetFrames(GetIDs(1000, 0))
    for i in range(len(poolIDs)):
        if not os.path.exists('ohlc'):
            os.makedirs('ohlc')
        if not os.path.exists('ticks'):
            os.makedirs('ticks')
        ohlcFrames[i].to_csv(os.path.join('ohlc', poolIDs[i] + '_ohlc.csv'))
        ticksFrames[i].to_csv(os.path.join('ticks', poolIDs[i] + '_ticks.csv'))
    dfPools.to_csv('poolsInfo.csv')


def testPlot():
    # having 5000 entries is pretty much impossible
    # if you know a way of tidying this i would be keen to see
    # right now, it crashes my computer from too much data
    GetFrames(GetIDs('1 skip:100', 0))
    x = ticksFrames[0]['tickIdx']
    y1 = ticksFrames[0]['liquidityGross']
    y2 = ticksFrames[0]['liquidityNet']
    plt.plot(x, y1)
    plt.plot(x, y2)
    plt.show()


# testPrint()
# testCSV()
# testPlot()#this needs attention, see comment in def

# server drop error
#  File "C:\Python38\lib\site-packages\gql\client.py", line 78, in execute
#    raise Exception(str(result.errors[0]))
#Exception: {'message': 'Failed to get entities from store: no connection to the server\n, query = "/* qid: d17c73ceec8ff10a-8185af0b902618c9 */\\nselect \'PoolHourData\' as entity, to_jsonb(c.*) as data from (\\nselect c.*, p.id::text as g$parent_id\\n/* children_type_b */  from unnest($1::text[]) as p(id) cross join lateral (select  *  from \\"sgd36572\\".\\"pool_hour_data\\" c where c.\\"block_range\\" @> $2 and p.id = c.\\"pool\\" order by \\"id\\", block_range\\n limit 1000) c) c\\n order by g$parent_id, \\"id\\" -- binds: [[\\"0x06729eb2424da47898f935267bd4a62940de5105\\"], 13685163]"'}
