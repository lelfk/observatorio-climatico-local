# Registro do planejamento e escopo da AE2

## Origem e continuidade acadêmica

Este documento registra as escolhas efetivas do **Observatório Climático Local**, desenvolvido individualmente e apoiado na apresentação e na transcrição da **Aula 1 do Projeto Integrador Extensionista 2**. A Aula 1 mostrou um slide sobre o **Projeto Integrador 1** apenas para relembrar a experiência da disciplina anterior; não afirmou que o observatório deve reproduzir o projeto de outro semestre. O enunciado da AE2, por sua vez, pede continuidade com o planejamento desta edição (AE1). Como não foi localizado um registro individual prévio desse planejamento, as decisões descritas aqui são **propostas documentadas nesta etapa**, sem simular um trabalho passado.

A transcrição da aula confirma que o projeto pode ser individual e que o planejamento inicial deve ficar registrado no repositório. As orientações detalhadas e seus momentos aproximados estão em [NOTAS_AULA1.md](NOTAS_AULA1.md).

## Problema e público beneficiário

**Questão central:** como transformar registros históricos de temperatura e chuva de uma localidade em informação acessível para discussões educativas sobre condições meteorológicas recentes?

**Público-alvo direto proposto:** comunidade escolar do Ipiranga, sobretudo estudantes e educadores. **Público indireto:** famílias que acompanhem as atividades educativas. Os dados podem apoiar aulas, exercícios e conversas retrospectivas sobre dias de maior calor ou chuva e as condições para atividades ao ar livre.

A proposta ainda não foi validada com representantes da comunidade; nenhuma escola, entrevista, declaração ou devolutiva foi alegada como concluída. Conforme a recomendação do professor na Aula 1, a verificação dessa necessidade e a comunicação dos resultados devem ser realizadas em etapas posteriores, sempre que possível.

## Recorte técnico

- Uma localidade: Ipiranga, São Paulo/SP. Ponto de referência: latitude -23.59139, longitude -46.60778; não representa uma estação meteorológica instalada no bairro.
- Intervalo contínuo de 30 dias: 1º a 30 de setembro de 2026, fuso America/Sao_Paulo.
- Três variáveis: temperatura mínima diária (°C), temperatura máxima diária (°C) e precipitação diária acumulada (mm).
- Uma tabela principal DuckDB, com chave primária na data e preservação de registros ausentes como NULL.
- Duas visualizações: série das mínimas/máximas e barras de precipitação diária.

## Perguntas e indicadores

1. **Qual foi a maior temperatura máxima e em que data?** KPI: maior máxima (°C). Consulta SQL do máximo e datas correspondentes.
2. **Quanto choveu no intervalo e quantos dias apresentaram precipitação?** KPI: precipitação acumulada (mm), com contagem auxiliar dos dias com chuva.
3. **Qual a temperatura média diária aproximada no período?** KPI: média das semissomas [(mínima + máxima)/2] (°C); não equivale à média de medições horárias.

## Critérios de sucesso

Coletar e documentar os 30 dias consecutivos, preservar o JSON bruto e metadados, validar duplicidades, datas, unidades, ausências e inconsistências, produzir consultas SQL e indicadores fundamentados, criar dois gráficos, gerar relatório de duas a quatro páginas e garantir reprodutibilidade pela automação online. A avaliação comunitária do material ainda é um objetivo de extensão, não um resultado comprovado.

## Limitações e ética

As séries da Open-Meteo são históricas e podem ser modeladas ou oriundas de reanálise; não se confundem com dados aferidos por estação meteorológica no Ipiranga. Trinta dias não sustentam afirmações sobre mudança climática plurianual nem previsão do tempo. O projeto não coleta dados pessoais; eventual feedback exigirá cuidados com consentimento, finalidade, minimização e divulgação. Qualquer associação entre fenômenos meteorológicos não demonstra causalidade.

## Registro de decisões e ajustes

Os slides e a transcrição reforçaram a escolha de escopo reduzido e reproduzível; mantivemos três variáveis, perguntas e KPIs e dois gráficos. Após a análise da transcrição, **refinamos** a descrição de público amplo (moradores, estudantes e educadores) para um público direto delimitado (estudantes e educadores), com famílias como público indireto. Também explicitamos que trabalho individual é permitido e que o painel Streamlit não é exigido na AE2, embora faça parte do projeto completo. Essas alterações são documentais; não houve substituição dos dados reais ou das regras de validação.

**Fonte didática:** transcrição fornecida pelo estudante, Aula 1, Projeto Integrador Extensionista 2; e enunciado de avaliação da AE2, páginas 1–4. **Fonte meteorológica:** [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api).
