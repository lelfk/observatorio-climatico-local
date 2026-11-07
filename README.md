# Observatório Climático Local

Projeto Integrador Extensionista 2 (AE2) com coleta, tratamento e análise de dados meteorológicos históricos do Ipiranga, São Paulo/SP.

O projeto utiliza Python, pandas, DuckDB e SQL. A execução automatizada é realizada pelo GitHub Actions, diretamente na nuvem.

## Escopo

| Item | Definição |
| --- | --- |
| Localidade | Ipiranga, São Paulo/SP |
| Coordenadas | Latitude -23.59139; longitude -46.60778 |
| Período | 01 a 30 de setembro de 2026 |
| Duração | 30 dias consecutivos |
| Fuso horário | \`America/Sao_Paulo\` |
| Variáveis | Temperatura mínima diária (°C), temperatura máxima diária (°C) e precipitação diária (mm) |
| Público-alvo | Estudantes e educadores da comunidade escolar do Ipiranga |
| Fonte | [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) |

## Objetivo

Organizar dados históricos de temperatura e precipitação para apoiar atividades didáticas sobre condições meteorológicas, episódios de chuva e calor e planejamento de atividades ao ar livre.

A análise responde a três perguntas:

1. Qual foi a maior temperatura máxima e em que data ocorreu?
2. Quanto choveu no período e em quantos dias houve precipitação?
3. Qual foi a temperatura média diária aproximada, calculada pela média das semissomas das temperaturas mínima e máxima?

## Executar online

1. Abra a aba [Actions](https://github.com/lelfk/observatorio-climatico-local/actions).
2. Selecione **Gerar relatório AE2 (Open-Meteo + DuckDB)**.
3. Clique em **Run workflow** e confirme a execução na branch \`main\`.
4. Aguarde a conclusão e confira os logs.
5. Consulte os arquivos gerados no repositório ou na seção Artifacts da execução.

O fluxo executa os testes, coleta os dados, trata e valida a série, atualiza o DuckDB, calcula os indicadores, gera os gráficos e produz o relatório PDF.

## Executar localmente

Requer Python 3.11 ou superior.

\`\`\`bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python coleta.py
python banco.py
python relatorio.py
\`\`\`

## Estrutura

\`\`\`text
.github/workflows/gerar_relatorio.yml   automação do processamento
config.json                              localidade, período e variáveis
coleta.py                                coleta e preservação do JSON original
banco.py                                 tratamento, validação e carga DuckDB
consultas.sql                            consultas e indicadores
relatorio.py                             gráficos, evidências e relatório PDF
requirements.txt                         dependências
tests/test_validacao.py                  testes automatizados
dados/originais/                         resposta original e metadados
dados/                                   CSV tratado, qualidade e banco DuckDB
dados/evidencias/                        resultados SQL, amostra e gráficos
docs/escopo-1/AE2/                       relatório final
\`\`\`

## Banco de dados

A tabela \`clima_diario\` possui \`data DATE\` como chave primária e armazena localidade, coordenadas, temperatura mínima, temperatura máxima e precipitação.

A carga utiliza \`INSERT ... ON CONFLICT(data) DO UPDATE\`, permitindo executar o processo novamente sem duplicar as datas.

## Validação

O processamento verifica:

- Presença das três variáveis e das 30 datas esperadas.
- Ausência de datas duplicadas ou fora do intervalo.
- Unidades de temperatura e precipitação.
- Valores numéricos e infinitos.
- Temperatura mínima superior à máxima.
- Precipitação negativa.
- Valores ausentes, preservados como \`NULL\`.

Os testes automatizados utilizam dados sintéticos exclusivamente para verificar essas regras. Eles não são utilizados no cálculo dos indicadores do relatório.

## Limitações

Os dados históricos da Open-Meteo são baseados em modelos e/ou reanálise e não correspondem necessariamente a medições realizadas por uma estação meteorológica instalada no Ipiranga. O intervalo de 30 dias permite descrever o período analisado, mas não sustenta conclusões sobre tendências climáticas de longo prazo. Dados históricos não constituem previsão meteorológica.

## Fontes

- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- [DuckDB](https://duckdb.org/docs/stable/)
- [GitHub Actions](https://docs.github.com/en/actions)
