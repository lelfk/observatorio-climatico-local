# Observatório Climático Local | Ipiranga, São Paulo/SP

**Projeto Integrador Extensionista 2 (AE2)**, com coleta de dados históricos, controle de qualidade, armazenamento em DuckDB, SQL, indicadores e relatório técnico em PDF. O projeto pode ser executado **inteiramente online pelo GitHub Actions**, sem instalar nada no computador.

> **Continuidade acadêmica:** o arquivo individual da AE1 não foi localizado. O escopo aqui adotado é uma **reconstrução proposta a partir da apresentação da Aula 1**, não um relato fictício de trabalho entregue. A validação com o professor e com o público beneficiário permanece pendente.

## Escopo

| Item | Definição |
| --- | --- |
| Localidade | Ipiranga, São Paulo/SP |
| Ponto de referência | Latitude -23.59139; longitude -46.60778 |
| Período | 01 a 30 de setembro de 2026 (30 dias) |
| Fuso | `America/Sao_Paulo` |
| Variáveis | Temperaturas mínima/máxima diárias (°C) e precipitação diária (mm) |
| Beneficiários propostos | Moradores, estudantes e educadores |
| Fonte | [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) |

**Três perguntas e KPIs:** qual foi a maior temperatura máxima (°C) e sua data? Quanto choveu (mm) e em quantos dias? Qual foi a temperatura média diária aproximada (°C), calculada pela média das semissomas de mínimas e máximas?

## Executar sem instalar nada

1. Entre na aba [Actions](https://github.com/lelfk/observatorio-climatico-local/actions).
2. Selecione **Gerar relatório AE2 (Open-Meteo + DuckDB)**.
3. Clique em **Run workflow** e execute na branch `main`.
4. Aguarde a execução concluir com indicador verde. Confira os logs e a seção de **Artifacts**.
5. Quando a execução for bem-sucedida, o fluxo também tentará publicar automaticamente no próprio repositório os dados reais, a base DuckDB, os resultados SQL, os gráficos e o relatório PDF em `docs/escopo-1/AE2/Relatorio_AE2_Observatorio_Climatico.pdf`.

O workflow também é iniciado após alterações relevantes no código. Se o GitHub solicitar ativação das Actions ou permissão para escrita, será necessário ajustar as configurações do repositório. **A existência do código não comprova a execução:** verifique o status verde e os arquivos efetivamente gerados.

## Arquivos do projeto

```text
.github/workflows/gerar_relatorio.yml   automação online e evidências
config.json                              localização, datas e variáveis
coleta.py                                requisição Requests, JSON bruto e metadados
banco.py                                 validação pandas e carga idempotente em DuckDB
consultas.sql                            três consultas e KPIs
relatorio.py                             indicadores, gráficos e relatório PDF
requirements.txt                         bibliotecas necessárias
.gitignore                               exclusões de segredos/ambiente temporário
tests/test_validacao.py                  cinco testes sintéticos de validação
dados/originais/                         JSON sem alteração + metadados UTC/SHA256
dados/                                   CSV, qualidade, indicadores, DuckDB
dados/evidencias/                        extrato da tabela, SQL e dois gráficos
docs/escopo-1/AE2/                       relatório final e planejamento reconstruído
```

Os arquivos sob `dados/` e o PDF final serão produzidos somente após uma execução bem-sucedida. **Valores artificiais são usados exclusivamente nos testes, nunca nos indicadores finais.**

## Executar no Codespaces, opcionalmente

Abra [github.dev](https://github.dev/lelfk/observatorio-climatico-local) para editar via navegador ou crie um Codespace, que permite abrir terminal na nuvem. Na pasta raiz:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python coleta.py
python banco.py
python banco.py
python relatorio.py
```

A segunda execução de `banco.py` verifica que não há duplicação de registros. Não é obrigatório usar terminal: prefira o workflow acima.

## Modelagem e validação

A tabela `clima_diario` possui a chave primária `data DATE`; campos de localidade e coordenadas; `temperatura_min_c`, `temperatura_max_c` e `precipitacao_mm` em `DOUBLE`. A carga usa `INSERT ... ON CONFLICT(data) DO UPDATE`, preservando a unicidade ao executar novamente. O pipeline rejeita datas fora do recorte, duplicações, unidades inesperadas, chuva negativa e mínima acima da máxima. Ausências permanecem NULL. São gerados `dados/qualidade.json`, `dados/indicadores.json` e evidências SQL.

## Limites e relevância extensionista

As séries históricas da Open-Meteo usam dados modelados/reanálise; não são necessariamente medições diretas de uma estação no bairro. Um único mês não caracteriza tendência climática duradoura e **histórico não é previsão**. A utilidade concreta dos resultados para a comunidade deverá ser avaliada em uma etapa de apresentação e feedback ainda não realizada. Nenhum dado pessoal é solicitado ou publicado.

## Fontes

- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- [DuckDB (documentação)](https://duckdb.org/docs/stable/)
- [GitHub Actions](https://docs.github.com/en/actions)
