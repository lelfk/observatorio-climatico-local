# Observatório Climático Local | Ipiranga, São Paulo/SP

**Projeto Integrador Extensionista 2 (AE2)**, com coleta de dados históricos, controle de qualidade, armazenamento em DuckDB, SQL, indicadores e relatório técnico em PDF. O projeto pode ser executado **inteiramente online pelo GitHub Actions**, sem instalar nada no computador.

> **Planejamento acadêmico:** o escopo foi definido a partir dos slides e da transcrição da **Aula 1 do Projeto Integrador Extensionista 2**. A aula apresenta o Projeto Integrador 1 somente como retrospectiva da disciplina anterior. Como não foi localizado um planejamento individual anterior da AE1, as escolhas feitas agora estão identificadas no [registro de planejamento](docs/escopo-1/AE2/PLANEJAMENTO_RECONSTRUIDO.md), sem atribuí-las a uma entrega prévia.

## Escopo

| Item | Definição |
| --- | --- |
| Localidade | Ipiranga, São Paulo/SP |
| Ponto de referência | Latitude -23.59139; longitude -46.60778 |
| Período | 01 a 30 de setembro de 2026 (30 dias) |
| Fuso | `America/Sao_Paulo` |
| Variáveis | Temperaturas mínima/máxima diárias (°C) e precipitação diária (mm) |
| Beneficiários propostos | Comunidade escolar do Ipiranga: estudantes e educadores (famílias como público indireto) |
| Fonte | [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) |

**Três perguntas e KPIs:** qual foi a maior temperatura máxima (°C) e sua data? Quanto choveu (mm) e em quantos dias? Qual foi a temperatura média diária aproximada (°C), calculada pela média das semissomas de mínimas e máximas?

## Objetivo, necessidade e público

**Modalidade:** desenvolvimento individual; repositório mantido pela conta `lelfk`. O professor explicou na Aula 1 que trabalhos individuais são permitidos e, para trabalhos em grupo, cada integrante deve fazer sua entrega.

**Questão extensionista:** como séries históricas locais podem ajudar estudantes e educadores a compreender episódios de calor e chuva? O produto organiza trinta dias de informações em indicadores e dois gráficos simples, úteis para discussões didáticas retrospectivas, inclusive sobre atividades ao ar livre. A necessidade ainda deve ser confirmada com representantes da comunidade escolar. Nenhuma entrevista, parceria com escola ou devolutiva é apresentada como realizada.

**Escopo da AE2:** coleta via API, tratamento e validação, uma tabela DuckDB, três perguntas/consultas SQL, três KPIs, dois gráficos e relatório de duas a quatro páginas. O painel Streamlit integra o projeto global apresentado na aula, mas **não é obrigatório nesta entrega AE2** conforme o enunciado específico.

A relação com a transcrição da aula está documentada em [notas da Aula 1](docs/escopo-1/AE2/NOTAS_AULA1.md), inclusive a distinção entre as atividades de estudo deste projeto e o antigo Projeto Integrador 1.

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
docs/escopo-1/AE2/                       relatório final, planejamento e notas da Aula 1
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

As séries históricas da Open-Meteo usam dados modelados/reanálise; não são necessariamente medições diretas de uma estação no bairro. Um único mês não caracteriza tendência climática duradoura e **histórico não é previsão**. A utilidade concreta dos resultados para a comunidade escolar deverá ser avaliada em uma etapa de apresentação e feedback ainda não realizada. Nenhum dado pessoal é solicitado ou publicado. A Aula 1 enfatiza a compreensão do problema, a rastreabilidade da origem, a documentação das dificuldades e a comunicação adequada para o público.

## Fontes

- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- [DuckDB (documentação)](https://duckdb.org/docs/stable/)
- [GitHub Actions](https://docs.github.com/en/actions)
