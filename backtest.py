import pandas as pd
import yfinance as yf
import os
import requests

def carregar_petr4(arquivo="petr4_historico.csv", ação="PETR4.SA", inicio="2016-01-01", fim="2026-09-16"):
    if os.path.exists(arquivo):
        return pd.read_csv(arquivo, header=[0, 1], index_col=0, parse_dates=True)
    df = yf.download(ação, start=inicio, end=fim)
    df.to_csv(arquivo)
    return df

def remover_dias_sem_pregao(df, ação):
    # faz com que o yf retorne algumas linhas que possuem volume zero, indicando dias sem pregão (feriados e similares)
    sem_pregao = df[df[("Volume", ação)] == 0]
    return df[df[("Volume", ação)] > 0], sem_pregao.index

def cdi_entre_pregoes(cdi, datas_pregao):
    # fator acumulado do CDI até o dia útil bancário anterior a cada data
    fator = (1 + cdi).cumprod().shift(1, fill_value=1.0)
    fator = fator.reindex(fator.index.union(datas_pregao)).ffill().reindex(datas_pregao)
    # CDI rendido entre o pregão anterior e o atual, incluindo dias úteis bancários sem pregão
    return fator / fator.shift(1) - 1

def baixar_cdi(inicio, fim):
    # série 12 do Banco Central é referente ao CDI diário, em % ao dia. Baixamos ano a ano porque a API limita o tamanho de cada consulta
    partes = []
    for ano in range(inicio.year, fim.year + 1):
        ini = max(inicio, pd.Timestamp(f"{ano}-01-01")).strftime("%d/%m/%Y")
        fi = min(fim, pd.Timestamp(f"{ano}-12-31")).strftime("%d/%m/%Y")
        url = ("https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
               f"?formato=json&dataInicial={ini}&dataFinal={fi}")
        partes.append(pd.DataFrame(requests.get(url, timeout=30).json()))
    cdi = pd.concat(partes)
    cdi["data"] = pd.to_datetime(cdi["data"], dayfirst=True)
    cdi["valor"] = cdi["valor"].astype(float) / 100  # transformando de porcentagem para decimal
    return cdi.set_index("data")["valor"]

def carregar_cdi(inicio, fim, arquivo="cdi_historico.csv"):
    if os.path.exists(arquivo):
        return pd.read_csv(arquivo, index_col=0, parse_dates=True).squeeze()
    cdi = baixar_cdi(inicio, fim)
    cdi.to_csv(arquivo)
    return cdi

def gerar_estrategia_de_retorno(precos, cdi, janela_curta, janela_longa, custo=0.001):
    ma_curta = precos.rolling(janela_curta).mean()
    ma_longa = precos.rolling(janela_longa).mean()
    sinal = (ma_curta > ma_longa).astype(int).shift(1)
    retorno_ativo = precos.pct_change()
    estrategia_de_retorno = sinal * retorno_ativo + (1 - sinal) * cdi # quando comprado é o retorno da acao, quando está fora do mercado é o CDI do dia
    trocas = sinal.diff().abs()
    estrategia_de_retorno -= trocas * custo
    return estrategia_de_retorno

'''calculamos o sharpe ratio para sabermos a relacao entre o retorno-risco no periodo, usando o retorno acima do CDI (excesso), ja que o CDI é o que se ganharia sem correr risco nenhum'''
def sharpe_ratio(retornos, livre_de_risco, dias_no_ano = 252):
    excesso = retornos - livre_de_risco.loc[retornos.index]
    return (excesso.mean() / excesso.std()) * (dias_no_ano ** 0.5) # poderia colocar o numero direto no 'return', mas nao faremos para evitar numeros mágicos no código.

'''calculamos o drawdown para medirmos a queda pico a pico, assim conseguimos observar qual foi a pior queda que alguem usando a estrategia que estamos fazendo sofreu'''
def max_drawdown(equity):
    pico_acumulado = equity.cummax()
    drawdown = equity / pico_acumulado - 1 #  calcula-se o equity em relacao ao maior pico ate o momento
    return drawdown.min(), drawdown

'''aqui vamos observar o retorno na metrica anual'''
def retorno_anualizado(equity, dias_no_ano = 252):
    n_dias = len(equity)
    return equity.iloc[-1] ** (dias_no_ano / n_dias) - 1 # pegamos o ultimo valor do equity (acumulado desde o inicio) para calcular o retorno anual