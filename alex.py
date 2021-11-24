from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pandas as pd
pd.set_option('display.max_rows', None)


client = Client(
            transport=RequestsHTTPTransport(
            url='https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3',
            verify=True,
            retries=5))

def tokenGet(qtyGet):
    '''Get quantity of tokens ordered by volumeUSD and store the ID's
    qtyGet: How many
    strGet: creates gql query for token ID
    idGet: Executes string
    idList: Parse out ID's and store in a list
    '''
    strGet = '{tokens(first:'+ str(qtyGet) +', orderBy:volumeUSD, orderDirection:desc){id}}'
    idGet = client.execute(gql(strGet))
    idList = []

    for i in range(0, qtyGet):
        idList.append(idGet['tokens'][i]['id'])


    '''Get info for each token in the idList and store it in the dataframe
    infoList: indexes all the token info into a list
    tempList: bundles info of one token to be saved in infoList
    strInfo: creates gql query for name, symbol, decimals
    info: executes the client for the token selected by i
    '''
    infoList = []
    for i in idList:
        tempList = []
        
        strInfo = '{tokens(where: {id: "' + i + '"}){name id symbol decimals}}'
        info = client.execute(gql(strInfo))
        
        name = info['tokens'][0]['name']
        id = info['tokens'][0]['id']
        symbol = info['tokens'][0]['symbol']
        decimals = info['tokens'][0]['decimals']
        tempList = [name, id, symbol, decimals]

        infoList.append(tempList)

    tokenFrame = pd.DataFrame(infoList)
    tokenFrame.columns = ['Name','ID','Symbol','Decimals']
    print(tokenFrame)

def poolGet(qtyGet):
    strGet = '{pools(first: '+str(qtyGet)+', orderBy:volumeUSD, orderDirection:desc) {id}}'
    idGet = client.execute(gql(strGet))
    idList = []

    for i in range(0, qtyGet):
        idList.append(idGet['pools'][i]['id'])  
    
    poolList = []
    for i in idList:
        tempList = []
        
        strInfo = '{pool(id: "'+i+'") {token0 {id symbol}token1 {id symbol}}}'
        info = client.execute(gql(strInfo))

        poolid = i
        token0id = info['pool']['token0']['id']
        token0symbol = info['pool']['token0']['symbol']
        token1id = info['pool']['token1']['id']
        token1symbol = info['pool']['token1']['symbol']

        tempList = [token0symbol, token1symbol, token0id, token1id, poolid]

        poolList.append(tempList)

    poolFrame = pd.DataFrame(poolList)
    poolFrame.columns = ['token0Symbol','token1Symbol','token0ID','token1ID', 'poolID']
    print(poolFrame)

def poolGetSymbol(token0symbol, token1symbol):
    token0Get = '{tokens(where:{symbol:"'+token0symbol+'"}){id}}'
    token1Get = '{tokens(where:{symbol:"'+token1symbol+'"}){id}}'
    token0Info = client.execute(gql(token0Get))
    token1Info = client.execute(gql(token1Get))
    token0IDs = []
    token1IDs = []
    poolIDs = []
    finalList = []

    for i in range(0, len(token0Info['tokens'])):
        token0IDs.append(token0Info['tokens'][i]['id'])

    for i in range(0, len(token1Info['tokens'])):
        token1IDs.append(token1Info['tokens'][i]['id'])
   
    if len(token0IDs) < len(token1IDs):
        token0IDs, token1IDs = token1IDs, token0IDs

    for i in token0IDs:
        for x in token1IDs:
            strInfo = '{pools(where: {token0: "'+i+'" token1: "'+x+'"}){id}}'
            swapInfo = '{pools(where: {token0: "'+x+'" token1: "'+i+'"}){id}}'
            info = client.execute(gql(strInfo))
            infoSwap = client.execute(gql(swapInfo))

            if len(info['pools']) > 0:
                for i in range(0, len(info['pools'])):
                    poolIDs.append(info['pools'][i]['id'])

            if len(infoSwap['pools']) > 0:
                for i in range(0, len(infoSwap['pools'])):
                    poolIDs.append(infoSwap['pools'][i]['id'])
            
    
    for i in poolIDs:
        poolStr = '{pool(id: "'+i+'"){token0{id symbol} token1{id symbol}}}'
        poolInfo = client.execute(gql(poolStr))
        
        poolid = i
        token0id = poolInfo['pool']['token0']['id']
        token0symbol = poolInfo['pool']['token0']['symbol']
        token1id = poolInfo['pool']['token1']['id']
        token1symbol = poolInfo['pool']['token1']['symbol']
        tempList = [token0symbol, token1symbol, token0id, token1id, poolid]

        finalList.append(tempList)

    poolsFrame = pd.DataFrame(finalList)
    poolsFrame.columns = ['token0Symbol','token1Symbol','token0ID','token1ID', 'poolID']
    print(poolsFrame)

#from what i can gather, first: is max 1000, and skip: is max 5000, so from my understanding you can get max 6000 entries
#may be able to sort, as lots of ticks are just 0,0 for liqG and liqN so filter the 0 entries to the bottom idk
#this function feels a bit janky, don't know if it's what is needed as i don't have a super deep understanding of where the limits of the data are
def poolGetTicks(poolID): 
    skip = 0
    finalList = []
    while True:
        strInfo = '{pool(id: "'+poolID+'"){ticks(first: 1000, skip: '+str(skip)+'){tickIdx liquidityNet liquidityGross}}}'
        tickInfo = client.execute(gql(strInfo))
        for i in range(len(tickInfo['pool']['ticks'])):

            liqG = tickInfo['pool']['ticks'][i]['liquidityGross']
            liqN = tickInfo['pool']['ticks'][i]['liquidityNet']
            tickIdx = tickInfo['pool']['ticks'][i]['tickIdx']
            tempList = [liqG, liqN, tickIdx]
            finalList.append(tempList)
        if skip == 5000:
            ticksFrame = pd.DataFrame(finalList)
            ticksFrame.columns = ['liquidityGross', 'liquidityNet', 'tickIdx']
            print(ticksFrame)
            return
        else:
            skip +=1000

#seems fine. for my test pool it cut off at 4862, so finished early and still created the DataFrame correctly.
def poolGetOHLC(poolID):
    skip = 0
    finalList = []
    while True:
        strInfo = '{pool(id: "'+poolID+'"){poolHourData(first: 1000, skip: '+str(skip)+'){periodStartUnix close high low open}}}'
        ohlcInfo = client.execute(gql(strInfo))
        
        for i in range(len(ohlcInfo['pool']['poolHourData'])):
            close = ohlcInfo['pool']['poolHourData'][i]['close']
            high = ohlcInfo['pool']['poolHourData'][i]['high']
            low = ohlcInfo['pool']['poolHourData'][i]['low']
            open = ohlcInfo['pool']['poolHourData'][i]['open']
            periodStartUnix = ohlcInfo['pool']['poolHourData'][i]['periodStartUnix']
            tempList = [close, high, low, open, periodStartUnix]
            finalList.append(tempList)
        if skip == 5000:
            ohlcFrame = pd.DataFrame(finalList)
            ohlcFrame.columns = ['Close', 'High', 'Low', 'Open', 'psUnix']
            print(ohlcFrame)
            return
        else:
            skip +=1000


#Try these out
#if you want to generate new pool IDs for Ticks and OHLC, run poolGet() to get the top volume pools, 
#or poolGetSymbol() to search for a pool ID by symbol still need to copy and paste the poolID from the printed DataFrame
#tokenGet(5)
#poolGet(10)
#poolGetSymbol('DAI', 'WETH')
#poolGetTicks('0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640')
#poolGetOHLC('0xcbcdf9626bc03e24f779434178a73a0b4bad62ed')

'''poolGet(10) poolIDs for reference
0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8
0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640
0x11b815efb8f581194ae79006d24e0d814b7697f6
0x4e68ccd3e89f51c3074ca5072bbac773960dfa36
0x60594a405d53811d3bc4766596efd80fd545a270
0x4585fe77225b41b697c938b018e2ac67ac5a20c0
0x7858e59e0c01ea06df3af3d20ac7b0003275d4bf
0xcbcdf9626bc03e24f779434178a73a0b4bad62ed
0xc2e9f25be6257c210d7adf0d4cd6e3e881ba25f8
0x6c6bc977e13df9b0de53b251522280bb72383700
'''

#just notes below, no functionality
#{pool(id: "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640") {token0 {id symbol}token1 {id symbol}}}

#pool
'{pools(where: {token0: "%s" token1: "%s" feeTier: %s}){id tick volumeUSD}}'
'{pools(first: 5, orderBy:volumeUSD, orderDirection:desc) {id token0{symbol} token1{symbol}}}'

#pool - ticks
'{pool(id: "%s"){ticks(first: 1000, skip: %s){tickIdx liquidityNet liquidityGross}}}'

#pool - hour data 
'{pool(id: "%s"){poolHourData(first: 1000, skip: %s){periodStartUnix close high low open}}}'


