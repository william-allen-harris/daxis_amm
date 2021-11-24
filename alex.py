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


    '''Stick it all in a dataframe
    infoFrame: Dataframe for the info
    '''
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




            





#Try these out
#tokenGet(5)
#poolGet(10)
poolGetSymbol('DAI', 'WETH')
poolGetSymbol('WETH', 'DAI')



#just notes below, no functionality

#{pool(id: "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640") {token0 {id symbol}token1 {id symbol}}}



#pool
'{pools(where: {token0: "%s" token1: "%s" feeTier: %s}){id tick volumeUSD}}'
'{pools(first: 5, orderBy:volumeUSD, orderDirection:desc) {id token0{symbol} token1{symbol}}}'

#pool - ticks
'{pool(id: "%s"){ticks(first: 1000, skip: %s){tickIdx liquidityNet liquidityGross}}}'

#pool - hour data 
'{pool(id: "%s"){poolHourData(first: 1000, skip: %s){periodStartUnix close high low open}}}'


