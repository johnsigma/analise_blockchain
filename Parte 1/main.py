import requests

basePath = 'https://blockchain.info'

lastBlockPath = basePath + '/latestblock'

# Requisição para pegar o último bloco da blockchain
lastBlockResp = requests.get(url=lastBlockPath)
lastBlockData = lastBlockResp.json()

lastBlockHash = lastBlockData['hash']

print(f'Hash do último bloco da blockchain: {lastBlockHash}')

# Hash utilizado no trabalho
# lastBlockHash = '000000000000000000024a9a60f3931b7c42736b4ac5f9eaa3704cfd27365fd2'

# Requisição para pegar as informações do último bloco
url2 = 'https://blockchain.info/rawblock/'+lastBlockHash
resp = requests.get(url=url2)
data = resp.json()

transactions = data['tx']

# A coinbase é a primeira transação de um bloco
coinbase = transactions[0]

print(f'\nHash da coinbase: {coinbase["hash"]}')
print('Mineradores que receberam a recompensa:')
for out in coinbase['out']:
    if 'addr' in out:
        print(f'Minerador {out["addr"]} recebeu {
              (out["value"] / 100000000):.8f} BTC')


for tx in transactions:

    txHash = tx['hash']

    # Ignorar a coinbase
    if txHash == coinbase['hash']:
        continue

    # Pega a taxa da transação
    fee = tx['fee']

    print(f'\nTransação {txHash}:')
    print(f'Taxa da transação: {(fee / 100000000):.8f} BTC')
    print('Número de entradas da transação:', len(tx['inputs']))
    print('Número de saídas da transação:', len(tx['out']))
