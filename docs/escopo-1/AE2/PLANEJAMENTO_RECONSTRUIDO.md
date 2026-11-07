# Planejamento reconstruído para a AE2

**Situação documental:** o único material da Aula 1 disponível foi a apresentação geral do professor. Não foi localizado relatório ou README do planejamento particular da AE1. Portanto, o presente recorte é uma **proposta desenvolvida agora**, não a transcrição de escolhas anteriores.

## Problema e motivação extensionista

Informações diárias sobre precipitação e temperatura, quando organizadas em indicadores de linguagem clara, podem apoiar a compreensão das condições meteorológicas recentes por estudantes, educadores e moradores do distrito do Ipiranga, em São Paulo. A necessidade específica ainda deve ser validada em conversa com o público-alvo; nenhuma consulta comunitária foi afirmada como realizada.

## Escopo

Uma localidade: Ipiranga, São Paulo/SP; ponto de referência -23.59139, -46.60778 (não uma estação meteorológica). 30 dias consecutivos: 01 a 30/09/2026. Três variáveis: temperatura mínima diária, temperatura máxima diária e precipitação acumulada diária. Uma tabela DuckDB com chave de data.

## Perguntas e indicadores

1. Qual a maior temperatura máxima e quando ocorreu? KPI: maior máxima (°C).
2. Qual o volume acumulado de precipitação e em quantos dias choveu? KPI: soma de precipitação (mm).
3. Qual a média diária aproximada das temperaturas no intervalo? KPI: média das semissomas de mínimas e máximas (°C). Não representa média horária observada.

## Critérios iniciais de sucesso

Verificar 30 datas consecutivas, nenhuma data duplicada, tipos e unidades corretos, validação física dos registros, execução de três consultas SQL e produção de indicadores interpretados. Avaliar compreensão e utilidade do resultado com beneficiários nas etapas seguintes, sem inventar depoimentos.

## Limitações e ética

Open-Meteo fornece histórico modelado ou de reanálise, não necessariamente observação de estação no bairro. Um mês não permite afirmar mudança climática de longo prazo. Análises históricas não são previsões. Não há coleta de dados pessoais; qualquer feedback futuro exige transparência, minimização e cuidado com consentimento e divulgação.

## Pendência acadêmica

Confirmar junto ao professor se a adoção do recorte reconstruído é aceita como continuidade da AE1; caso exista uma AE1 entregue, alinhar esta proposta ao documento original antes da submissão.
