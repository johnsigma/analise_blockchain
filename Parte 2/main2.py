import copy
from datetime import datetime
import altair as alt
import os
import json
import pandas as pd
from main import ler_arquivo, calculaHistoricoSaldo, plotar_grafico_linha, plotar_grafico_area, plotar_grafico_histograma, imprimir_historico_saldo
import pickle


def clusterizar_enderecos(enderecos):

    toCluster = {}
    cc = {}

    for endereco in enderecos:

        toCluster[endereco['address']] = []
        for tx in endereco['txs']:
            temp = [i['prev_out']['addr'] for i in tx['inputs']]
            if endereco['address'] in temp:
                toCluster[endereco['address']].append(temp)

        n_tx = endereco['n_tx']
        done = len(endereco['txs'])

        while done < n_tx:
            for tx in endereco['txs']:
                temp = [i['prev_out']['addr'] for i in tx['inputs']]
                if endereco['address'] in temp:
                    toCluster[endereco['address']].append(temp)

            done += len(endereco['txs'])

    for endereco in enderecos:
        # print('--------------------------')
        clusters = []
        cc[endereco['address']] = []

        for tx in toCluster[endereco['address']]:

            c = []
            for i in range(len(clusters)):
                if any(x in clusters[i] for x in tx):
                    c.append(i)

            if len(c) == 0:
                clusters.append(tx)
            else:
                x = c[0]
                del c[0]

                clusters[x].extend(tx)

                for i in c:
                    clusters[x].extend(clusters[i])

                clusters[x] = list(set(clusters[x]))

            # print(endereco['address'])
            cluster = copy.deepcopy(clusters[0])
            cluster = [x for x in cluster if x != endereco['address']]
            setCluster = set(cluster)
            cc[endereco['address']].extend(list(setCluster))

    return cc


def main():
    base_path = 'rawaddr/'

    data_enderecos = ler_arquivo(base_path)

    # print(enderecos)

    clusters = clusterizar_enderecos(data_enderecos)

    cluster = clusters['1JHH1pmHujcVa1aXjRrA13BJ13iCfgfBqj']
    print(len(cluster))

    with open('cluster.pkl', 'wb') as f:
        pickle.dump(cluster, f)

    transacoes = []

    for endereco in data_enderecos:
        if endereco['address'] in cluster:
            transacoes.extend(endereco['txs'])

    historico_saldo = calculaHistoricoSaldo(transacoes, cluster)

    plotar_grafico_linha(historico_saldo, 'h1')

    imprimir_historico_saldo(historico_saldo)


if __name__ == '__main__':
    main()
