# Confronto da transcrição da Aula 1 com a implementação

**Material:** transcrição textual de aproximadamente 40 minutos da live introdutória do Projeto Integrador Extensionista 2, disponibilizada pelo estudante. Os tempos abaixo são aproximados, pois a transcrição apresenta marcações de tempo irregulares. Este arquivo sintetiza as instruções, não reproduz a fala integral.

| Momento na live | Orientação da Aula 1 | Aplicação no projeto |
| --- | --- | --- |
| ~1min | Projeto individual ou em grupo é permitido; se houver grupo, cada estudante deve enviar | Repositório identificado como trabalho individual |
| ~5–7min | Extensão pressupõe público e necessidade, não apenas gráficos; se possível, conversar com representantes | Público direto delimitado: comunidade escolar; validação comunitária registrada como pendente |
| ~7–9min | Pipeline integrado: coleta, base, consultas SQL, painel e documentação | Coleta + pandas + DuckDB + SQL + gráficos + PDF; Streamlit reservado para etapa posterior |
| ~9–11min | Uma localidade, 30 dias consecutivos, projeto simples e reproduzível | Ipiranga/SP, 01–30/09/2026, três variáveis |
| ~11–14min | Três perguntas devem orientar a análise; exemplos do docente não são modelos rígidos; sem inferência causal indevida | Três perguntas próprias, três indicadores, dois gráficos; limites explicitados |
| ~17–19min | README deve permitir entender arquivos e reproduzir o projeto; organização de pastas é flexível | README completo, execução online por GitHub Actions, estrutura documentada |
| ~22–24min | Commits importantes; algumas etapas de revisão de equipes não são cobradas de pessoa sozinha | Histórico de commits, sem exigir pull request artificial |
| ~28–30min | Planejamento e escolhas devem ser registrados desde o começo | Registro em PLANEJAMENTO_RECONSTRUIDO.md |
| ~33–35min | Três KPIs e dois gráficos; Streamlit será apresentado como painel da solução completa; relatório documenta limitações/dificuldades | Consultas, indicadores, gráficos e relatório AE2 com limites explícitos |

## Distinções que afetam a entrega

O professor cita o **Projeto Integrador 1** como lembrança de uma disciplina anterior, ao passo que o trabalho atual é o **Projeto Integrador Extensionista 2**. A sigla **AE1** no enunciado da atividade atual se refere ao planejamento da fase precedente **desta edição**, que não foi localizado entre os materiais enviados. Portanto, o relatório não deve afirmar que um planejamento individual anterior foi entregue ou que a comunidade já foi consultada.

A live apresenta o painel como componente da **solução completa ao longo das etapas**. Já o enunciado específico da **AE2**, na página 3, determina que não é obrigatória, nesta etapa, a entrega de um painel Streamlit nem a devolutiva final à comunidade. A orientação específica da atividade rege a entrega atual.

A aula recomenda selecionar até três variáveis, três perguntas e KPIs e dois gráficos. O projeto atende a esses parâmetros com dados históricos da Open-Meteo, SQL e base DuckDB. O professor também recomenda documentar o que não foi verificado, inclusive a necessidade comunitária, sem supor participação de pessoas ou inferir relação de causa e efeito a partir de 30 dias de dados.

## Mudanças realizadas após leitura da live

1. Relatório PDF: contextualização mais fiel do projeto, público direto explicitado e contato comunitário declarado como etapa futura.
2. README: autoria individual, objetivo, público e explicação sobre a diferença entre AE2 e projeto completo.
3. Planejamento: registro detalhado do recorte e esclarecimento da referência ao antigo Projeto Integrador 1.
4. Configuração: mudança editorial do campo de público beneficiário; datas, coordenadas, variáveis, base e indicadores originais permanecem iguais.

**Não houve mudança dos resultados meteorológicos com a reinterpretação da aula.** Qualquer nova execução gera os indicadores a partir da fonte original documentada.
