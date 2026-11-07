# Observatório Climático Local | Ipiranga, São Paulo/SP

Projeto Integrador Extensionista 2 (AE2) com coleta e análise de dados meteorológicos históricos. O processamento utiliza Python, pandas, DuckDB e SQL para gerar indicadores, gráficos e um relatório técnico em PDF. A execução pode ser realizada online pelo GitHub Actions, sem instalação no computador.

## Escopo

| Item | Definição |
| --- | --- |
| Localidade | Ipiranga, São Paulo/SP |
| Ponto de referência | Latitude -23.59139; longitude -46.60778 |
| Período | 01 a 30 de setembro de 2026 |
| Duração | 30 dias consecutivos |
| Fuso horário | `America/Sao_Paulo` |
| Variáveis | Temperatura mínima diária (°C), temperatura máxima diária (°C) e precipitação diária (mm) |
| Público-alvo | Estudantes e educadores da comunidade escolar do Ipiranga |
| Fonte de dados | [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) |

## Objetivo e análise

O projeto organiza dados históricos de temperatura e precipitação de um ponto de referência no Ipiranga. Os resultados permitem observar os dias de maior temperatura, o volume de chuva no período e a variação das temperaturas mínimas e máximas. Os indicadores e gráficos podem apoiar atividades didáticas sobre condições meteorológicas e planejamento de atividades ao ar livre.

A análise responde a três perguntas: qual foi a maior temperatura máxima e em que data ocorreu; quanto choveu no período e em quantos dias houve precipitação; e qual foi a temperatura média diária aproximada, calculada pela média das semissomas das temperaturas mínima e máxima.

## Executar pelo GitHub Actions

1. Acesse a aba [Actions](https://github.com/lelfk/observatorio-climatico-local/actions).
2. Selecione **Gerar relatório AE2 (Open-Meteo + DuckDB)**.
3. Clique em **Run workflow** e execute na branch `main`.
4. Aguarde a conclusão e confira os logs e os artefatos publicados.
5. O workflow gera os dados tratados, a base DuckDB, os resultados SQL, os gráficos e o relatório PDF em `docs/escopo-1/AE2/Relatorio_AE2_Observatorio_Climatico.pdf`.

O workflow também é iniciado após alterações nos arquivos de código e configuração. A execução bem-sucedida pode ser conferida na aba Actions.

## Estrutura do projeto

```text
.github/workflows/gerar_relatorio.yml   automação de coleta e geração dos resultados
config.json                              localidade, período e variáveis
coleta.py                                consulta à API e preservação do JSON original
banco.py                                 validação dos dados e carga no DuckDB
consultas.sql                            consultas SQL e indicadores
relatorio.py                             gráficos e relatório PDF
requirements.txt                         dependências Python
tests/test_validacao.py                  testes de validação
dados/originais/                         resposta original da API e metadados
dados/                                   dados tratados, indicadores e banco DuckDB
dados/evidencias/                        resultados SQL, amostra e gráficos
docs/escopo-1/AE2/                       relatório final em PDF
```

Os arquivos de dados e o relatório são atualizados após a execução do workflow. Dados sintéticos são utilizados somente nos testes de validação e não entram no cálculo dos indicadores.

## Modelagem e validação

A tabela `clima_diario` utiliza `data DATE` como chave primária e armazena localidade, coordenadas, temperatura mínima, temperatura máxima e precipitação. A carga utiliza `INSERT ... ON CONFLICT(data) DO UPDATE`, evitando duplicação de datas em execuções sucessivas.

O processamento verifica o intervalo de datas, registros duplicados, unidades, valores numéricos, temperaturas mínimas superiores às máximas e precipitação negativa. Valores ausentes são preservados como `NULL`. Os resultados da validação ficam registrados em `dados/qualidade.json`.

## Limitações

Os dados históricos da Open-Meteo são baseados em modelos e/ou reanálise e não correspondem necessariamente a medições realizadas por uma estação meteorológica instalada no Ipiranga. O período de 30 dias permite descrever as condições observadas nesse intervalo, mas não sustenta conclusões sobre tendências climáticas de longo prazo. Dados históricos também não constituem previsão meteorológica. O projeto não coleta dados pessoais.

## Fontes

- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- [DuckDB](https://duckdb.org/docs/stable/)
- [GitHub Actions](https://docs.github.com/en/actions)
