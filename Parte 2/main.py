import copy
from datetime import datetime
import pickle
import altair as alt
import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def ler_arquivo(base_path):

    lista_dict = []

    for nome_arquivo in os.listdir(base_path):
        if nome_arquivo.endswith('.json'):
            caminho_arquivo = os.path.join(base_path, nome_arquivo)
            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                conteudo_json = json.load(arquivo)
                lista_dict.append(conteudo_json)

    return lista_dict


def clusterizar_enderecos(enderecos):

    toCluster = {}
    cc = {}

    for endereco in enderecos:

        toCluster[endereco['address']] = []
        for tx in endereco['txs']:
            temp = [i['prev_out']['addr'] for i in tx['inputs']]
            # temp.extend([i['addr'] for i in tx['out']])
            if endereco['address'] in temp:
                toCluster[endereco['address']].append(temp)

        n_tx = endereco['n_tx']
        done = len(endereco['txs'])

        while done < n_tx:
            for tx in endereco['txs']:
                temp = [i['prev_out']['addr'] for i in tx['inputs']]
                # temp.extend([i['addr'] for i in tx['out']])
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

            cc[endereco['address']].extend(clusters[0])

    return cc


def calculaHistoricoSaldo(transacoes, cluster):
    hashs_calculados = []
    transacoes_relevantes = []

    for transacao in transacoes:
        hash_transacao = transacao['hash']

        entradas_no_cluster = False
        saidas_no_cluster = False

        if hash_transacao in hashs_calculados:
            continue

        hashs_calculados.append(hash_transacao)

        for entrada in transacao.get('inputs', []):
            endereco = entrada['prev_out'].get('addr')
            if endereco in cluster:
                entradas_no_cluster = True
                break

        for saida in transacao.get('out', []):
            endereco = saida.get('addr')
            if endereco in cluster:
                saidas_no_cluster = True
                break

        if entradas_no_cluster or saidas_no_cluster:
            transacoes_relevantes.append({
                'time': transacao['time'],
                'hash': hash_transacao,
                'entradas_no_cluster': entradas_no_cluster,
                'saidas_no_cluster': saidas_no_cluster,
                'inputs': transacao.get('inputs', []),
                'out': transacao.get('out', [])
            })

    transacoes_relevantes.sort(key=lambda x: x['time'])

    historico_saldo = []
    saldo_atual = 0

    for transacao in transacoes_relevantes:
        if transacao['entradas_no_cluster']:
            for entrada in transacao['inputs']:
                if entrada['prev_out']['addr'] in cluster:
                    saldo_atual -= entrada['prev_out']['value']

        if transacao['saidas_no_cluster']:
            for saida in transacao['out']:
                if saida.get('addr') in cluster:
                    saldo_atual += saida['value']

        historico_saldo.append(
            (datetime.fromtimestamp(transacao['time']), saldo_atual/100000000, transacao['hash']))

    return historico_saldo


# def calculaHistoricoSaldo(transacoes, cluster):
#     hashs_calculados = []
#     transacoes_relevantes = []

#     for transacao in transacoes:
#         hash_transacao = transacao['hash']

#         if hash_transacao in hashs_calculados:
#             continue

#         hashs_calculados.append(hash_transacao)

#         transacoes_relevantes.append({
#             'time': transacao['time'],
#             'hash': hash_transacao,
#             'inputs': transacao.get('inputs', []),
#             'out': transacao.get('out', [])
#         })

#     transacoes_relevantes.sort(key=lambda x: x['time'])

#     historico_saldo = []
#     saldo_atual = 0

#     for transacao in transacoes_relevantes:
#         for entrada in transacao['inputs']:
#             if entrada['prev_out']['addr'] in cluster:
#                 saldo_atual -= entrada['prev_out']['value']

#         for saida in transacao['out']:
#             if saida.get('addr') in cluster:
#                 saldo_atual += saida['value']

#         historico_saldo.append(
#             (datetime.fromtimestamp(transacao['time']), saldo_atual/100000000, transacao['hash']))

#     return historico_saldo


def plotar_grafico_linha(historico_saldo, nome):
    tempos_datetime = [t[0] for t in historico_saldo]
    saldos = [saldo[1] for saldo in historico_saldo]

    df = pd.DataFrame({'Tempo': tempos_datetime, 'Saldo': saldos})

    chart = alt.Chart(df).mark_line().encode(
        x=alt.X('Tempo:T', title='Tempo'),
        y=alt.Y('Saldo:Q', title='Saldo(em BTC)'),
        tooltip=['Tempo', 'Saldo']
    ).properties(
        title='Histórico de saldo do cluster'
    ).interactive()

    chart.save(f'linha_{nome}.html')


def plotar_grafico_area(historico_saldo):
    tempos_datetime = [t[0] for t in historico_saldo]
    saldos = [saldo[1] for saldo in historico_saldo]

    df = pd.DataFrame({'Tempo': tempos_datetime, 'Saldo': saldos})

    chart = alt.Chart(df).mark_area().encode(
        x=alt.X('Tempo:T', title='Tempo'),
        y=alt.Y('Saldo:Q', title='Saldo(em BTC)'),
        tooltip=['Tempo', 'Saldo']
    ).properties(
        title='Histórico de saldo do cluster'
    ).interactive()

    chart.save('area.html')


def plotar_grafico_histograma(historico_saldo):
    tempos_datetime = [t[0] for t in historico_saldo]
    saldos = [saldo[1] for saldo in historico_saldo]

    df = pd.DataFrame({'Tempo': tempos_datetime, 'Saldo': saldos})

    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('Tempo:T', title='Tempo'),
        y=alt.Y('Saldo:Q', title='Saldo(em BTC)'),
        tooltip=['Tempo', 'Saldo']
    ).properties(
        title='Distribuição de saldo do cluster'
    ).interactive()

    chart.save('hist.html')


def imprimir_historico_saldo(historico_saldo):
    for item in historico_saldo:
        print(f'Data: {item[0].strftime(
            "%d/%m/%Y %H:%M:%S")}, Saldo: {item[1]} BTC, Transação: {item[2]}')


def naoRepetidos(cluster_h1, cluster):
    set_cluster = set(cluster)
    set_cluster_h1 = set(cluster_h1)

    unique_in_cluster = set_cluster - set_cluster_h1
    unique_in_cluster_h1 = set_cluster_h1 - set_cluster

    return [(item, 'cluster') for item in unique_in_cluster] + [(item, 'cluster_h1') for item in unique_in_cluster_h1]


def calcular_indice_gini(valores):
    # Converte a lista para um array numpy e ordena os valores
    valores = np.array(valores)
    valores_ordenados = np.sort(valores)

    # Calcula os índices
    n = len(valores)

    # Calcula a soma dos produtos dos valores ordenados
    soma_produtos = np.sum((2 * np.arange(1, n+1) - n - 1) * valores_ordenados)

    # Calcula o índice de Gini
    gini = soma_produtos / (n * np.sum(valores_ordenados))

    return gini


def curva_lorenz(values):
    # Ordena os valores e calcula a soma cumulativa
    values = np.array(values)
    values_sorted = np.sort(values)

    # Soma cumulativa dos valores
    cum_values = np.cumsum(values_sorted)

    # Normaliza para que o total seja 1
    cum_values_normalized = cum_values / cum_values[-1]

    # Adiciona um ponto (0, 0) ao início da curva
    lorenz_curve = np.insert(cum_values_normalized, 0, 0)

    return lorenz_curve


def plota_curva_lorenz(values):
    # Obtém a curva de Lorenz
    lorenz = curva_lorenz(values)

    # Eixo x: proporção da população
    x = np.linspace(0, 1, len(lorenz))

    # Plotando a curva de Lorenz
    plt.figure(figsize=(8, 6))
    plt.plot(x, lorenz, label='Curva de Lorenz', color='blue')

    # Linha de igualdade perfeita (linha de 45°)
    plt.plot([0, 1], [0, 1], label='Igualdade perfeita',
             color='red', linestyle='--')

    # Preenchendo a área entre a curva de Lorenz e a linha de igualdade
    plt.fill_between(x, lorenz, x, color='lightblue', alpha=0.5)

    # Personalizando o gráfico
    plt.title("Curva de Lorenz")
    plt.xlabel("Proproção dos endereços")
    plt.ylabel("Proporção da riqueza")
    plt.legend()

    # Exibe o gráfico
    plt.show()


# def valores_por_endereco(cluster, transacoes):
#     valoresPorEndereco = {}

#     for endereco in cluster:
#         valoresPorEndereco[endereco] = 0

#         for transacao in transacoes:
#             for entrada in transacao['inputs']:
#                 if entrada['prev_out']['addr'] == endereco:
#                     valoresPorEndereco[endereco] -= entrada['prev_out']['value']
#             for saida in transacao['out']:
#                 if saida.get('addr') == endereco:
#                     valoresPorEndereco[endereco] += saida['value']

#     return valoresPorEndereco

def valores_por_endereco(cluster, transacoes):
    valoresPorEndereco = {endereco: 0 for endereco in cluster}

    for transacao in transacoes:
        for entrada in transacao['inputs']:
            if entrada['prev_out']['addr'] in cluster:
                valoresPorEndereco[entrada['prev_out']
                                   ['addr']] -= entrada['prev_out']['value']
        for saida in transacao['out']:
            if saida.get('addr') in cluster:
                valoresPorEndereco[saida['addr']] += saida['value']

    for endereco, valor in valoresPorEndereco.items():
        if valor < 0:
            valoresPorEndereco[endereco] = 0
        else:
            valoresPorEndereco[endereco] = valor / 100000000
    return valoresPorEndereco


def main():
    base_path = 'rawaddr/'

    data_enderecos = ler_arquivo(base_path)

    # print(enderecos)

    clusters = clusterizar_enderecos(data_enderecos)

    # print(len(clusters))

    cluster = clusters['1JHH1pmHujcVa1aXjRrA13BJ13iCfgfBqj']

    set_cluster = set(cluster)
    cluster = list(set_cluster)

    transacoes = []

    for endereco in data_enderecos:
        if endereco['address'] in cluster:
            transacoes.extend(endereco['txs'])

    historico_saldo = calculaHistoricoSaldo(
        transacoes, cluster)

    # plotar_grafico_linha(historico_saldo, 'not_h1')

    # imprimir_historico_saldo(historico_saldo)

    valores = valores_por_endereco(cluster, transacoes)

    # print(json.dumps(valores, indent=4))

    valores_transacoes = list(valores.values())
    indice_gini = calcular_indice_gini(valores_transacoes)
    print(f'Índice de Gini: {indice_gini}')

    plota_curva_lorenz(valores_transacoes)


if __name__ == '__main__':
    main()
