# B3 Systematic Strategy Backtest

Projeto de portfólio com backtests sistemáticos de estratégias quantitativas aplicadas a ações da B3 (bolsa brasileira). Cada capítulo do repositório testa uma estratégia diferente, com o mesmo rigor metodológico: sem look-ahead bias, validação out-of-sample via walk-forward, e métricas de retorno-risco reais comparadas contra um benchmark de buy-and-hold.

## Capítulo 1 — MA Crossover (PETR4)

O primeiro capítulo testa uma estratégia de cruzamento de médias móveis (MA crossover) aplicada à PETR4 (Petrobras), no período de 01/01/2016 a 16/09/2026.

### Metodologia

- **Dados**: preços diários de fechamento da PETR4.SA, obtidos via `yfinance` e fixados em `petr4_historico.csv` para garantir reprodutibilidade (a API pode retornar dados um pouco diferentes no futuro).
- **Sinal**: cruzamento de duas médias móveis, quando a média curta fica acima da média longa, a estratégia assume posição comprada; caso contrário, fica fora do mercado. O sinal é defasado em um dia (`shift(1)`) para evitar look-ahead bias, já que a decisão só pode ser tomada com o fechamento do dia já conhecido.
- **Motor de backtest**: o retorno da estratégia é o retorno do ativo multiplicado pelo sinal (0 ou 1), descontado um custo de transação de 0,5% aplicado toda vez que a posição muda.
- **Walk-forward validation**: em vez de escolher a melhor combinação de janelas (10/50 ou 20/100) olhando o histórico inteiro, o notebook usa uma janela de treino de 600 dias para escolher a combinação com melhor retorno, e testa essa escolha apenas no período seguinte de 200 dias (nunca visto na decisão). A janela desliza 200 dias a cada iteração, gerando uma série out-of-sample contínua.
- **Métricas**: Sharpe ratio, máximo drawdown e retorno anualizado, calculados tanto para a estratégia quanto para o benchmark (buy-and-hold da PETR4 no mesmo período coberto pelo
  walk-forward).

### Resultados (out-of-sample, walk-forward)

| Métrica               | Estratégia (MA crossover) | Benchmark (buy-and-hold) |
|-----------------------|---------------------------|--------------------------|
| Sharpe ratio          | 0.36                      | 0.78                     |
| Máximo drawdown       | -39.07%                   | -63.36%                  |
| Retorno anualizado    | 6.54%                     | 26.67%                   |

### Conclusão

A estratégia teve um risco de cauda (tail risk) bem menor que o benchmark, sendo o pior drawdown quase metade do drawdown do buy-and-hold. Em troca, tanto o retorno anualizado quanto o Sharpe ficaram bem abaixo do buy-and-hold.

Esse é o trade-off esperado de qualquer estratégia trend-following: ela reduz a exposição em quedas fortes, mas paga esse seguro entrando atrasada nas tendências (o sinal só surge depois que a média cruza, perdendo o início do movimento e o momento ideal para compra ou venda da ação) e sofrendo whipsaw (efeito chicote) em períodos sem direção clara. Esse trade-off só compensa quando existem quedas realmente severas no período analisado, o que não foi o caso da PETR4 nesse período de cerca de 10 anos, marcados por uma alta excepcionalmente forte e sustentada. Uma estratégia MA crossover tende a ser mais interessante para ativos com histórico de quedas sustentadas e prolongadas, e não quedas repentinas, já que o atraso natural das médias móveis a torna lenta demais para reagir a um crash rápido.

## Próximos capítulos

- **Mean-reversion**: estratégia baseada na tendência de reversão à média de curto prazo, testando
  se desvios extremos de preço tendem a ser corrigidos.
- **Momentum cross-sectional**: comparação de momentum relativo entre múltiplos ativos da B3,
  selecionando os de melhor/pior desempenho relativo em vez de operar um ativo isolado.

## Como rodar localmente

```bash
# clonar o repositório
git clone https://github.com/amenescal/b3-systematic-strategy-backtest.git
cd b3-systematic-strategy-backtest

# criar e ativar o ambiente virtual
python3 -m venv venv
source venv/bin/activate  # no Windows: venv\Scripts\activate

# instalar as dependências
pip install -r requirements.txt

# abrir o notebook
jupyter lab b3-systematic-strategy-backtest.ipynb
```

O notebook já inclui um snapshot dos dados (`petr4_historico.csv`), então não é necessário
reconsultar a API do Yahoo Finance para reproduzir os resultados — mas a célula de download
também pode ser executada novamente, caso queira dados mais recentes.
