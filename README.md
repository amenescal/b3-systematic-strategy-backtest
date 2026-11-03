# B3 Systematic Strategy Backtest

Projeto de portfólio com backtests sistemáticos de estratégias quantitativas aplicadas a ações da B3 (bolsa brasileira). Cada capítulo do repositório testa uma estratégia diferente, com o mesmo rigor metodológico: sem look-ahead bias, validação out-of-sample via walk-forward, métricas de retorno-risco comparadas contra o buy-and-hold e contra o CDI, e testes de robustez do resultado.

## Estrutura do repositório

- `b3-systematic-strategy-backtest.ipynb`: capítulo 1 (MA crossover na PETR4).
- `b3-systematic-strategy-backtest-mean-reversion.ipynb`: capítulo 2 (mean reversion), em desenvolvimento.
- `backtest.py`: funções compartilhadas entre os capítulos (carregamento e limpeza dos dados, CDI, sinal, retorno da estratégia, walk-forward, métricas, carteira passiva e bootstrap).
- `petr4_historico.csv` e `cdi_historico.csv`: snapshots dos dados usados nos resultados.

## Capítulo 1 — MA Crossover (PETR4)

O primeiro capítulo testa uma estratégia de cruzamento de médias móveis (MA crossover) aplicada à PETR4 (Petrobras), com dados de 04/01/2016 a 15/09/2026.

### Metodologia

- **Dados**: preços diários de fechamento da PETR4.SA, ajustados por proventos, obtidos via `yfinance`, e a série diária do CDI (série 12 do SGS, Banco Central). Os dois históricos ficam salvos em `petr4_historico.csv` e `cdi_historico.csv`, e o código lê esses arquivos quando eles existem, consultando as APIs apenas se eles não existirem. Assim, qualquer pessoa que rodar o código parte exatamente dos mesmos dados e chega aos mesmos resultados.
- **Limpeza dos dados**: foram removidas 10 linhas, todas entre maio de 2017 e janeiro de 2018, em que o `yfinance` incluiu dias sem pregão (em sua maioria feriados) com volume zero e o preço apenas repetido do dia anterior. Também há 11 dias entre março e abril de 2016 com abertura, máxima, mínima e fechamento iguais, quase sempre com volume muito abaixo do normal, o que sugere dados incompletos na fonte; eles foram mantidos porque houve pregão, e estão no período de aquecimento das médias, fora do período out-of-sample.
- **Sinal**: quando a média móvel curta fica acima da longa, a estratégia assume posição comprada; caso contrário, fica fora do mercado. O sinal é defasado em um dia (`shift(1)`) para evitar look-ahead bias, já que a decisão só pode ser tomada com o fechamento do dia já conhecido.
- **Caixa remunerado pelo CDI**: nos dias fora do mercado, o capital rende o CDI, como renderia na prática em um investimento pós-fixado. Entre o fechamento de um pregão e o do pregão seguinte, o caixa rende o CDI acumulado de todos os dias úteis bancários do intervalo, inclusive os dias em que os bancos abriram e a B3 não (como 24/12 e 31/12).
- **Custo de transação**: 0,1% a cada mudança de posição. As taxas da B3 somadas ao spread da PETR4 ficam em torno de 0,05% por operação; o valor foi dobrado como margem conservadora para execução pior que a média.
- **Walk-forward validation**: nove combinações de médias (curtas de 5, 10 e 20 dias com longas de 50, 100 e 200 dias) são avaliadas em uma janela de treino de 600 pregões, e a de maior Sharpe no treino é aplicada nos 200 pregões seguintes, nunca vistos na decisão. A janela desliza 200 pregões a cada iteração, gerando uma série out-of-sample contínua. Os primeiros 200 pregões são usados apenas como aquecimento, para que todas as médias móveis já existam no início do primeiro treino. O walk-forward devolve o sinal de cada janela de teste, e o retorno, com o custo de transação, é calculado uma única vez sobre o sinal concatenado, para que as trocas de posição entre janelas sejam cobradas corretamente.
- **Métricas**: Sharpe ratio (calculado sobre o retorno acima do CDI), máximo drawdown e retorno anualizado, todos no mesmo período coberto pelo walk-forward.
- **Benchmarks**: buy-and-hold da PETR4, CDI e uma carteira passiva com a mesma exposição média à ação que a estratégia teve, com o restante no CDI, rebalanceada diariamente. A carteira passiva isola o efeito do timing: ela mostra o resultado de ter a mesma exposição média sem nenhuma decisão de entrada e saída. Sua exposição só é conhecida no fim do período, então ela serve apenas como referência de comparação, e não como estratégia implementável.
- **Robustez**: (1) comparação do walk-forward com cada uma das nove combinações mantida fixa no período out-of-sample; (2) sensibilidade ao ponto de início das janelas, rodando o walk-forward com 20 deslocamentos (de 0 a 190 pregões, de 10 em 10) e comparando todos no período de datas comum a eles; (3) bootstrap pareado em blocos de 20 pregões (5.000 reamostragens) da diferença de Sharpe entre a estratégia e o buy-and-hold.

### Resultados (out-of-sample, walk-forward, 02/04/2019 a 25/06/2026)

| Métrica                     | Estratégia (MA crossover) | Carteira passiva (68% PETR4) | Buy-and-hold PETR4 | CDI     |
|-----------------------------|---------------------------|------------------------------|--------------------|---------|
| Retorno anualizado          | 9.06%                     | 22.43%                       | 25.60%             | 9.59%   |
| Sharpe ratio (sobre o CDI)  | 0.12                      | 0.55                         | 0.55               | —       |
| Máximo drawdown             | -39.96%                   | -47.47%                      | -63.36%            | 0.00%   |

A estratégia ficou comprada em 67.9% dos dias, com 37 mudanças de posição (cerca de 18 operações completas). A combinação escolhida variou entre as janelas: 20/200 foi escolhida 3 vezes, e 20/100, 10/50 e 20/50 foram escolhidas 2 vezes cada.

O Sharpe da carteira passiva é igual ao do buy-and-hold por construção: misturar a ação com CDI em proporção fixa reduz o excesso de retorno e o risco na mesma proporção.

### Análises de robustez

- **Combinações fixas**: mantidas fixas durante todo o período out-of-sample, as nove combinações tiveram Sharpe entre -0.01 (10/100) e 0.38 (10/200), com mediana de 0.19. O walk-forward (0.12) superou apenas uma delas. Ou seja, o Sharpe na janela de treino não ajudou a prever qual combinação funcionaria na janela seguinte. Essa tabela é apenas diagnóstica: escolher agora a melhor combinação seria usar o período de teste para definir o parâmetro.
- **Sensibilidade ao alinhamento das janelas**: no período comum aos 20 deslocamentos (07/01/2020 a 27/11/2025, com CDI de 9.58% ao ano), o resultado varia bastante com o ponto de início, mas a estratégia ficou abaixo do CDI em todos eles, com excesso entre -1.45 e -11.48 pontos percentuais por ano e Sharpe entre -0.28 e 0.09.
- **Significância estatística**: a diferença de Sharpe entre a estratégia e o buy-and-hold é de -0.43, com intervalo de confiança de 95% de [-1.07, 0.27] pelo bootstrap. A diferença não é significativa a 95%, mas a estratégia superou o buy-and-hold em apenas 10% das reamostragens.

### Conclusão

A estratégia de MA crossover não agregou valor na PETR4 no período analisado. Ela rendeu 9.06% ao ano, abaixo dos 9.59% do CDI, mesmo ficando comprada em cerca de 68% dos dias, e teve Sharpe de 0.12, contra 0.55 do buy-and-hold.

A única vantagem aparente, o drawdown menor que o do buy-and-hold, perde força na comparação com a carteira passiva de mesma exposição: sem nenhum timing, ela teria rendido 22.43% ao ano, com Sharpe de 0.55 e drawdown de -47.47%. O timing comprou poucos pontos de proteção a um custo de cerca de 13 pontos percentuais de retorno por ano.

O mecanismo é o trade-off típico de estratégias trend-following: o sinal só surge depois que as médias cruzam, então a estratégia entra atrasada nas altas e sofre com whipsaw (efeito chicote) em períodos sem direção clara. Nesta amostra, a estratégia evitou boa parte do crash de março de 2020, quando o buy-and-hold teve sua pior queda, mas sofreu a própria pior queda entre janeiro de 2021 e março de 2023, um período em que a PETR4 subiu cerca de 49%, justamente por causa do whipsaw.

A conclusão se mantém sob diferentes alinhamentos das janelas, e a seleção de parâmetros pelo walk-forward não agregou valor em relação a combinações fixas. Os resultados valem para um único ativo, em um único período, e não permitem concluir que o MA crossover não funciona em geral, apenas que não funcionou aqui.

### Limitações conhecidas

- **Um único ativo e um único período**: os resultados não se generalizam para outras ações ou outros regimes de mercado.
- **Poucas operações**: com cerca de 18 operações completas em 7 anos, as métricas têm incerteza alta, como mostra o intervalo do bootstrap.
- **Execução no fechamento**: o backtest assume que a operação é feita no mesmo preço de fechamento usado para calcular o sinal. Na prática, isso exigiria operar no leilão de fechamento; uma versão mais conservadora executaria na abertura do dia seguinte.
- **Impostos não modelados**: o imposto de renda sobre ganhos de capital não foi considerado, nem para a estratégia nem para o buy-and-hold.
- **Qualidade dos dados**: os dados vêm do `yfinance`, que apresentou linhas espúrias em 2017–2018 (removidas) e dias aparentemente incompletos em 2016 (mantidos, fora do período out-of-sample).

### Revisão (novembro de 2026)

A primeira versão deste capítulo foi revisada com três correções e quatro análises novas.

Correções: (1) remoção das 10 linhas de dias sem pregão; (2) acúmulo do CDI entre pregões consecutivos, em vez de usar o CDI de um único dia; (3) cálculo do custo de transação sobre o sinal concatenado do walk-forward, o que eliminou uma cobrança indevida em 12/11/2024 e passou a cobrar a entrada no primeiro dia do período out-of-sample. Análises novas: carteira passiva de mesma exposição, combinações fixas, sensibilidade ao alinhamento das janelas e bootstrap. O código também passou a ser organizado em funções no `backtest.py`.

| Métrica                        | Versão original           | Versão revisada           |
|--------------------------------|---------------------------|---------------------------|
| Período out-of-sample          | 19/03/2019 a 11/06/2026   | 02/04/2019 a 25/06/2026   |
| Estratégia: retorno anualizado | 9.86%                     | 9.06%                     |
| Estratégia: Sharpe             | 0.15                      | 0.12                      |
| Estratégia: máximo drawdown    | -41.50%                   | -39.96%                   |
| Buy-and-hold: retorno / Sharpe | 26.60% / 0.57             | 25.60% / 0.55             |
| CDI: retorno anualizado        | 9.47%                     | 9.59%                     |

A mudança de período vem da remoção das 10 linhas, que desloca as janelas do walk-forward em 10 pregões. A principal mudança de conclusão: a versão original afirmava que a estratégia rendeu cerca de 0.4 ponto percentual por ano acima do CDI. A análise de sensibilidade mostrou que esse número dependia do alinhamento específico das janelas; com os dados corrigidos, a estratégia fica abaixo do CDI no período principal e em todos os 20 alinhamentos testados no período comum.

## Próximos capítulos

- **Mean reversion**: estratégia baseada na tendência de reversão à média de curto prazo, testando se desvios extremos de preço tendem a ser corrigidos.
- **Momentum cross-sectional**: comparação de momentum relativo entre múltiplos ativos da B3, selecionando os de melhor e pior desempenho relativo em vez de operar um ativo isolado.

Para que os capítulos sejam comparáveis, todos usam a mesma infraestrutura (`backtest.py`), são avaliados no mesmo período out-of-sample do capítulo 1 e passam pelas mesmas análises de robustez. A grade de parâmetros de cada estratégia será registrada neste README antes de os resultados serem calculados.

## Como rodar localmente

```bash
# clonar o repositório
git clone https://github.com/amenescal/b3-systematic-strategy-backtest.git
cd b3-systematic-strategy-backtest

# criar e ativar o ambiente virtual
python3.14 -m venv venv
source venv/bin/activate  # no Windows: venv\Scripts\activate

# instalar as dependências
pip install -r requirements.txt

# abrir o notebook
jupyter lab b3-systematic-strategy-backtest.ipynb
```

O notebook também pode ser aberto no VS Code, selecionando o kernel do `venv`.

O repositório já inclui os snapshots dos dados (`petr4_historico.csv` e `cdi_historico.csv`), então não é necessário consultar o Yahoo Finance nem o Banco Central para reproduzir os resultados. Para usar dados mais recentes, basta apagar os arquivos CSV e rodar o notebook novamente: ele baixa os dados e salva novos snapshots. Dados novos mudam os resultados, inclusive pelo deslocamento das janelas do walk-forward.
