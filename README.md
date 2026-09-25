# B3 Systematic Strategy Backtest

Projeto de portfólio com backtests sistemáticos de estratégias quantitativas aplicadas a ações da B3 (bolsa brasileira). Cada capítulo do repositório testa uma estratégia diferente, com o mesmo rigor metodológico: sem look-ahead bias, validação out-of-sample via walk-forward e métricas de retorno-risco comparadas contra o buy-and-hold e contra o CDI.

## Capítulo 1 — MA Crossover (PETR4)

O primeiro capítulo testa uma estratégia de cruzamento de médias móveis (MA crossover) aplicada à PETR4 (Petrobras), com dados de 01/01/2016 a 16/09/2026.

### Metodologia

- **Dados**: preços diários de fechamento da PETR4.SA, ajustados por proventos, obtidos via `yfinance`, e a série diária do CDI (série 12 do SGS, Banco Central). Os dois históricos ficam salvos em `petr4_historico.csv` e `cdi_historico.csv`, e o notebook lê esses arquivos quando eles existem, consultando as APIs apenas se eles não existirem. Assim, qualquer pessoa que rodar o código parte exatamente dos mesmos dados e chega aos mesmos resultados.
- **Sinal**: quando a média móvel curta fica acima da longa, a estratégia assume posição comprada; caso contrário, fica fora do mercado. O sinal é defasado em um dia (`shift(1)`) para evitar look-ahead bias, já que a decisão só pode ser tomada com o fechamento do dia já conhecido.
- **Caixa remunerado pelo CDI**: nos dias fora do mercado, o capital rende o CDI, como renderia na prática em um investimento pós-fixado. O CDI de cada data remunera o dinheiro até o dia útil seguinte, por isso também é defasado em um dia.
- **Custo de transação**: 0,1% a cada mudança de posição. As taxas da B3 somadas ao spread da PETR4 ficam em torno de 0,05% por operação; o valor foi dobrado como margem conservadora para execução pior que a média.
- **Walk-forward validation**: nove combinações de médias (curtas de 5, 10 e 20 dias com longas de 50, 100 e 200 dias) são avaliadas em uma janela de treino de 600 dias, e a de maior Sharpe no treino é testada nos 200 dias seguintes, nunca vistos na decisão. A janela desliza 200 dias a cada iteração, gerando uma série out-of-sample contínua. Os primeiros 200 dias da série são usados apenas como aquecimento, para que todas as médias móveis já existam no início do primeiro treino e as combinações sejam comparadas em condições iguais.
- **Métricas**: Sharpe ratio (calculado sobre o retorno acima do CDI), máximo drawdown e retorno anualizado, para a estratégia, para o buy-and-hold da PETR4 e para o CDI, todos no mesmo período coberto pelo walk-forward.

### Resultados (out-of-sample, walk-forward, 19/03/2019 a 11/06/2026)

| Métrica                     | Estratégia (MA crossover) | Buy-and-hold PETR4 | CDI     |
|-----------------------------|---------------------------|--------------------|---------|
| Retorno anualizado          | 9.86%                     | 26.60%             | 9.47%   |
| Sharpe ratio (sobre o CDI)  | 0.15                      | 0.57               | —       |
| Máximo drawdown             | -41.50%                   | -63.36%            | 0.00%   |

A combinação escolhida variou entre as janelas: 20/200 foi escolhida 3 vezes, e 20/100, 10/50 e 20/50 foram escolhidas 2 vezes cada, o que indica que nenhum par de médias foi consistentemente superior ao longo do período.

### Conclusão

A estratégia reduziu a pior queda em cerca de um terço em relação ao buy-and-hold (-41.50% contra -63.36%), mas o resultado mais importante é a comparação com o CDI: ela rendeu apenas cerca de 0.4 ponto percentual por ano acima do que se teria sem correr risco nenhum. Ou seja, a proteção nas quedas custou quase todo o prêmio de se expor à ação.

Esse é o trade-off típico de estratégias trend-following: o sinal só surge depois que as médias cruzam, então a estratégia entra atrasada nas altas e sofre com whipsaw (efeito chicote) em períodos sem direção clara. Numa ação que teve uma alta forte e sustentada como a PETR4 nesse período, esse custo pesou mais do que o benefício da proteção.

Uma hipótese que esses dados não permitem testar, por usarem um único ativo em um único período, é que o MA crossover funcione melhor em ativos com quedas longas e graduais, nas quais o atraso das médias ainda permite reagir antes da maior parte da perda, e pior em quedas bruscas. Além disso, com cerca de 7 anos de dados out-of-sample, o erro padrão do Sharpe anualizado fica em torno de 0.4, então a diferença entre 0.15 e 0.57 sugere, mas não permite afirmar com confiança estatística, que o buy-and-hold foi superior.

### Limitações conhecidas

- **Um único ativo e um único período**: os resultados não se generalizam para outras ações ou outros regimes de mercado.
- **Execução no fechamento**: o backtest assume que a operação é feita no mesmo preço de fechamento usado para calcular o sinal. Na prática, isso exigiria operar no leilão de fechamento; uma versão mais conservadora executaria na abertura do dia seguinte.
- **Troca de combinação sem custo**: quando o walk-forward muda de combinação na virada entre duas janelas de teste e as duas estão em posições diferentes, essa operação implícita não paga custo de transação.
- **Impostos não modelados**: o imposto de renda sobre ganhos de capital não foi considerado, nem para a estratégia nem para o buy-and-hold.

## Próximos capítulos

- **Mean-reversion**: estratégia baseada na tendência de reversão à média de curto prazo, testando se desvios extremos de preço tendem a ser corrigidos.
- **Momentum cross-sectional**: comparação de momentum relativo entre múltiplos ativos da B3, selecionando os de melhor e pior desempenho relativo em vez de operar um ativo isolado.

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

O repositório já inclui os snapshots dos dados (`petr4_historico.csv` e `cdi_historico.csv`), então não é necessário consultar o Yahoo Finance nem o Banco Central para reproduzir os resultados. Para usar dados mais recentes, basta apagar os arquivos CSV e rodar o notebook novamente: ele baixa os dados e salva novos snapshots.
