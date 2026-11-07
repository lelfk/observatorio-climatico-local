"""Gera gráficos, indicadores e o relatório técnico da AE2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from coleta import ROOT, carregar_configuracao, caminhos_dos_dados

matplotlib.use("Agg")


def formatar_numero(valor: Any) -> str:
        if valor is None or pd.isna(valor):
                        return "não disponível"
    return f"{float(valor):.1f}".replace(".", ",")


def carregar_resultados(caminho_banco: Path) -> tuple[pd.DataFrame, list[pd.DataFrame]]:
    """Executa as três consultas SQL e retorna também a série diária."""
    caminho_sql = ROOT / "consultas.sql"
    comandos = [
        comando.strip()
        for comando in caminho_sql.read_text(encoding="utf-8").split(";")
        if comando.strip()
    ]
    if len(comandos) != 3:
        raise ValueError("O arquivo consultas.sql deve conter exatamente três consultas.")

    with duckdb.connect(str(caminho_banco), read_only=True) as conexao:
        serie = conexao.execute(
            "SELECT * FROM clima_diario ORDER BY data"
        ).df()
        resultados = [
            conexao.execute(comando).df()
            for comando in comandos
        ]

    if len(serie) != 30 or serie["data"].duplicated().any():
        raise ValueError("O banco precisa conter 30 datas únicas.")
    if resultados[0].empty or pd.isna(resultados[0]["maior_temperatura_c"].iloc[0]):
        raise ValueError("Não há temperaturas válidas para calcular a maior máxima.")

    return serie, resultados


def calcular_indicadores(
    config: dict[str, Any],
    resultados: list[pd.DataFrame],
) -> dict[str, Any]:
    """Organiza os resultados das consultas em um dicionário de indicadores."""
    maior_temperatura = resultados[0]
    chuva = resultados[1].iloc[0]
    temperatura = resultados[2].iloc[0]

    return {
        "fonte": "Open-Meteo Historical Weather API",
        "localidade": config["localidade"],
        "periodo": [config["inicio"], config["fim"]],
        "maior_temperatura_maxima_c": float(
            maior_temperatura["maior_temperatura_c"].iloc[0]
        ),
        "datas_maior_maxima": [
            str(data)[:10] for data in maior_temperatura["data"].tolist()
        ],
        "precipitacao_total_mm": (
            None if pd.isna(chuva["precipitacao_total_mm"])
            else float(chuva["precipitacao_total_mm"])
        ),
        "dias_com_chuva": int(chuva["dias_com_chuva"]),
        "dias_com_dado_precipitacao": int(chuva["dias_com_dado"]),
        "temperatura_media_aproximada_c": (
            None if pd.isna(temperatura["temperatura_media_aproximada_c"])
            else float(temperatura["temperatura_media_aproximada_c"])
        ),
        "dias_termicos_validos": int(temperatura["dias_validos"]),
        "amplitude_termica_media_c": (
            None if pd.isna(temperatura["amplitude_termica_media_c"])
            else float(temperatura["amplitude_termica_media_c"])
        ),
    }


def gerar_graficos(serie: pd.DataFrame, pasta_saida: Path) -> tuple[Path, Path]:
    """Gera os gráficos de temperatura e precipitação."""
    pasta_saida.mkdir(parents=True, exist_ok=True)
    datas = pd.to_datetime(serie["data"])

    fig, eixo = plt.subplots(figsize=(8.4, 2.15), dpi=145)
    eixo.plot(
        datas,
        serie["temperatura_min_c"],
        label="Temperatura mínima",
        linewidth=1.7,
    )
    eixo.plot(
        datas,
        serie["temperatura_max_c"],
        label="Temperatura máxima",
        linewidth=1.7,
    )
    eixo.set_ylabel("°C")
    eixo.grid(alpha=0.2)
    eixo.legend(loc="upper left", fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()

    caminho_temperaturas = pasta_saida / "temperaturas.png"
    fig.savefig(caminho_temperaturas)
    plt.close(fig)

    fig, eixo = plt.subplots(figsize=(8.4, 2.15), dpi=145)
    eixo.bar(datas, serie["precipitacao_mm"], width=0.7)
    eixo.set_ylabel("mm")
    eixo.grid(axis="y", alpha=0.2)
    fig.autofmt_xdate()
    fig.tight_layout()

    caminho_precipitacao = pasta_saida / "precipitacao.png"
    fig.savefig(caminho_precipitacao)
    plt.close(fig)

    return caminho_temperaturas, caminho_precipitacao


def salvar_evidencias(
    serie: pd.DataFrame,
    resultados: list[pd.DataFrame],
    indicadores: dict[str, Any],
    pasta_saida: Path,
) -> None:
    """Salva indicadores, amostra da tabela e resultados das consultas."""
    pasta_saida.mkdir(parents=True, exist_ok=True)

    (ROOT / "dados" / "indicadores.json").write_text(
        json.dumps(indicadores, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    serie.head(6).to_csv(
        pasta_saida / "amostra_banco.csv",
        index=False,
        encoding="utf-8",
    )

    partes = []
    for numero, resultado in enumerate(resultados, start=1):
        partes.append(
            f"CONSULTA {numero}\n{resultado.to_string(index=False)}"
        )

    (pasta_saida / "consultas_sql.txt").write_text(
        "\n\n".join(partes) + "\n",
        encoding="utf-8",
    )


def criar_estilos():
    """Define os estilos tipográficos do documento."""
    estilos = getSampleStyleSheet()
    estilos.add(
        ParagraphStyle(
            name="TituloProjeto",
            parent=estilos["Title"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#12334A"),
            spaceAfter=13,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="SecaoProjeto",
            parent=estilos["Heading2"],
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#087E85"),
            spaceBefore=8,
            spaceAfter=7,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="TextoProjeto",
            parent=estilos["Normal"],
            fontSize=8.7,
            leading=12.8,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="NotaProjeto",
            parent=estilos["Normal"],
            fontSize=7.6,
            leading=10.7,
            textColor=colors.HexColor("#566675"),
            spaceAfter=7,
        )
    )
    return estilos


def adicionar_tabela(
    elementos: list,
    linhas: list[list[Any]],
    larguras: list[float],
) -> None:
    """Adiciona uma tabela com cabeçalho e linhas alternadas."""
    tabela = Table(linhas, colWidths=larguras, hAlign="LEFT", repeatRows=1)
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12334A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#EEF4F6")],
                ),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elementos.append(tabela)


def gerar_relatorio(
    config: dict[str, Any],
    metadados: dict[str, Any],
    qualidade: dict[str, Any],
    serie: pd.DataFrame,
    resultados: list[pd.DataFrame],
    indicadores: dict[str, Any],
    graficos: tuple[Path, Path],
) -> Path:
    """Monta o relatório PDF com metodologia, resultados e limitações."""
    pasta_pdf = ROOT / "docs" / "escopo-1" / "AE2"
    pasta_pdf.mkdir(parents=True, exist_ok=True)
    caminho_pdf = pasta_pdf / "Relatorio_AE2_Observatorio_Climatico.pdf"

    documento = SimpleDocTemplate(
        str(caminho_pdf),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.7 * cm,
        title="Observatório Climático Local - AE2",
    )
    estilos = criar_estilos()
    elementos = []

    def paragrafo(texto: str, estilo: str = "TextoProjeto") -> None:
        elementos.append(Paragraph(texto, estilos[estilo]))

    def secao(titulo: str) -> None:
        paragrafo(titulo, "SecaoProjeto")

    def rodape(canvas, doc) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#C9D9E2"))
        canvas.line(2 * cm, 1.35 * cm, 19 * cm, 1.35 * cm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#556979"))
        canvas.drawString(
            2 * cm,
            1.05 * cm,
            "Observatório Climático Local | Projeto Integrador Extensionista 2",
        )
        canvas.drawRightString(19 * cm, 1.05 * cm, f"Página {doc.page}")
        canvas.restoreState()

    chuva = resultados[1].iloc[0]
    temperatura = resultados[2].iloc[0]
    datas_maximas = ", ".join(indicadores["datas_maior_maxima"])

    paragrafo(
        "OBSERVATÓRIO CLIMÁTICO LOCAL<br/>AE2 | Relatório técnico e analítico",
        "TituloProjeto",
    )
    secao("1. Contexto e objetivo")
    paragrafo(
        "Este projeto reúne e analisa registros meteorológicos históricos do "
        "Ipiranga, São Paulo/SP, com foco em temperatura e precipitação. O objetivo "
        "é disponibilizar informações organizadas para apoiar estudantes e "
        "educadores da comunidade escolar em atividades didáticas sobre condições "
        "meteorológicas, episódios de chuva e calor e planejamento de atividades "
        "ao ar livre."
    )

    secao("2. Recorte, questões e indicadores")
    paragrafo(
        f"<b>Localidade:</b> {config['localidade']} "
        f"(latitude {config['latitude']}, longitude {config['longitude']}). "
        f"<b>Período:</b> {config['inicio']} a {config['fim']}, 30 dias consecutivos. "
        f"<b>Fuso:</b> {config['timezone']}. <b>Variáveis:</b> temperaturas "
        "mínima/máxima diárias (°C) e precipitação diária acumulada (mm)."
    )
    paragrafo(
        "Perguntas: (1) qual foi a temperatura máxima mais alta e quando ocorreu? "
        "(2) quanto choveu no período e em quantos dias houve chuva? "
        "(3) qual foi a temperatura média diária aproximada? Indicadores principais: "
        "maior máxima (°C), precipitação acumulada (mm) e média das semissomas "
        "diárias das temperaturas mínima e máxima (°C)."
    )

    secao("3. Fonte e coleta de dados")
    paragrafo(
        "Os dados foram obtidos pela <b>Open-Meteo Historical Weather API</b>, "
        "por requisição GET no Python com a biblioteca Requests, informando "
        "coordenadas, datas, variáveis e fuso. A resposta original em JSON foi "
        "preservada sem alteração e teve seu SHA-256 registrado em arquivo de metadados."
    )
    paragrafo(
        f"<b>Evidência:</b> coleta em UTC {metadados.get('coletado_em_utc', 'não informado')}, "
        f"HTTP {metadados.get('status_http', 'não informado')}; "
        f"SHA-256 {metadados.get('sha256', '')[:24]}…"
    )
    elementos.append(PageBreak())

    paragrafo("Tratamento, armazenamento e evidências", "TituloProjeto")
    secao("4. Tratamento e controle de qualidade")
    paragrafo(
        "O pandas organizou as variáveis, converteu datas e tipos numéricos, "
        "conferiu unidades, comparou os 30 dias esperados com as datas retornadas "
        "e rejeitou duplicidades e inconsistências. Valores ausentes foram "
        "preservados como NULL."
    )
    paragrafo(
        f"<b>Resultado:</b> {qualidade['registros']} registros; cobertura temporal "
        f"{qualidade['cobertura_temporal_pct']}%; datas duplicadas: "
        f"{qualidade['datas_duplicadas']}; datas faltantes: "
        f"{qualidade['dias_faltantes']}; ausências por variável: {qualidade['nulos']}."
    )

    secao("5. Estrutura e carga DuckDB")
    paragrafo(
        "A tabela <b>clima_diario</b> contém data DATE (chave primária), localidade "
        "VARCHAR, latitude e longitude DOUBLE, temperatura_min_c DOUBLE, "
        "temperatura_max_c DOUBLE e precipitacao_mm DOUBLE. A carga atualiza "
        "registros existentes pela data, evitando duplicações em reexecuções."
    )
    linhas_amostra = [["Data", "Mín. (°C)", "Máx. (°C)", "Chuva (mm)"]]
    for _, registro in serie.head(4).iterrows():
        linhas_amostra.append(
            [
                str(registro["data"])[:10],
                formatar_numero(registro["temperatura_min_c"]),
                formatar_numero(registro["temperatura_max_c"]),
                formatar_numero(registro["precipitacao_mm"]),
            ]
        )
    adicionar_tabela(
        elementos,
        linhas_amostra,
        [4.1 * cm, 4 * cm, 4 * cm, 4.9 * cm],
    )

    secao("6. Séries históricas")
    elementos.append(Image(str(graficos[0]), width=16.4 * cm, height=4.2 * cm))
    elementos.append(Spacer(1, 0.2 * cm))
    elementos.append(Image(str(graficos[1]), width=16.4 * cm, height=4.2 * cm))
    paragrafo(
        "Gráficos derivados dos registros consultados e carregados no DuckDB. "
        "Não são medições diretas de uma estação instalada no distrito.",
        "NotaProjeto",
    )
    elementos.append(PageBreak())

    paragrafo("Análise e aplicação extensionista", "TituloProjeto")
    secao("7. Consultas SQL e resultados")
    adicionar_tabela(
        elementos,
        [
            ["KPI / consulta", "Resultado", "Unidade"],
            [
                "Maior temperatura máxima",
                f"{formatar_numero(indicadores['maior_temperatura_maxima_c'])} "
                f"({datas_maximas})",
                "°C",
            ],
            [
                "Precipitação acumulada",
                formatar_numero(indicadores["precipitacao_total_mm"]),
                "mm",
            ],
            [
                "Temperatura média aproximada",
                formatar_numero(indicadores["temperatura_media_aproximada_c"]),
                "°C",
            ],
        ],
        [7.7 * cm, 7 * cm, 2.3 * cm],
    )
    paragrafo(
        f"A primeira consulta selecionou a maior temperatura máxima: "
        f"{formatar_numero(indicadores['maior_temperatura_maxima_c'])} °C, "
        f"em {datas_maximas}. A segunda somou {formatar_numero(chuva['precipitacao_total_mm'])} mm "
        f"de chuva, com precipitação em {int(chuva['dias_com_chuva'])} dias. "
        f"A terceira calculou a média aproximada de "
        f"{formatar_numero(temperatura['temperatura_media_aproximada_c'])} °C "
        f"em {int(temperatura['dias_validos'])} dias completos. "
        "As consultas estão disponíveis em consultas.sql e seus resultados "
        "em dados/evidencias/consultas_sql.txt."
    )

    secao("8. Critérios de sucesso e interpretação")
    paragrafo(
        "A base contém 30 registros únicos, com cobertura integral do período "
        "e unidades coerentes. O processamento verifica ausências e inconsistências, "
        "executa três consultas SQL e gera três indicadores e dois gráficos. "
        "A média das semissomas de mínimas e máximas é aproximada e não corresponde "
        "à média horária observada."
    )

    secao("9. Aplicação, ética e limites")
    paragrafo(
        "Os indicadores e gráficos podem subsidiar atividades didáticas sobre "
        "episódios de calor e precipitação, interpretação de séries históricas "
        "e planejamento de atividades ao ar livre. A análise é descritiva e "
        "restrita ao período selecionado. O projeto não coleta dados pessoais."
    )
    paragrafo(
        "A Open-Meteo fornece séries meteorológicas baseadas em modelos/reanálise "
        "para um ponto geográfico; não há comprovação de que os valores sejam "
        "observações de estação no Ipiranga. Um intervalo de 30 dias não permite "
        "inferir tendências climáticas multianuais, e esta análise histórica "
        "não constitui previsão meteorológica."
    )

    secao("10. Fontes e reprodutibilidade")
    paragrafo(
        "Open-Meteo Historical Weather API: https://open-meteo.com/en/docs/historical-weather-api. "
        "DuckDB: https://duckdb.org/docs/stable/. "
        "GitHub Actions: https://docs.github.com/en/actions. "
        "Código, dados originais, consultas SQL e evidências: "
        "https://github.com/lelfk/observatorio-climatico-local."
    )

    documento.build(elementos, onFirstPage=rodape, onLaterPages=rodape)
    return caminho_pdf


def executar() -> None:
    """Gera os indicadores, gráficos, evidências e relatório PDF."""
    config = carregar_configuracao()
    caminho_json, caminho_metadados = caminhos_dos_dados(config)
    caminho_banco = ROOT / "dados" / "observatorio.duckdb"
    caminho_qualidade = ROOT / "dados" / "qualidade.json"

    arquivos_necessarios = [
        caminho_json,
        caminho_metadados,
        caminho_banco,
        caminho_qualidade,
    ]
    for caminho in arquivos_necessarios:
        if not caminho.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {caminho}. "
                "Execute coleta.py e banco.py antes de gerar o relatório."
            )

    metadados = json.loads(caminho_metadados.read_text(encoding="utf-8"))
    qualidade = json.loads(caminho_qualidade.read_text(encoding="utf-8"))

    serie, resultados = carregar_resultados(caminho_banco)
    indicadores = calcular_indicadores(config, resultados)

    pasta_evidencias = ROOT / "dados" / "evidencias"
    salvar_evidencias(serie, resultados, indicadores, pasta_evidencias)
    graficos = gerar_graficos(serie, pasta_evidencias)

    caminho_pdf = gerar_relatorio(
        config=config,
        metadados=metadados,
        qualidade=qualidade,
        serie=serie,
        resultados=resultados,
        indicadores=indicadores,
        graficos=graficos,
    )

    print(f"Relatório gerado: {caminho_pdf}")
    print("Indicadores:")
    print(json.dumps(indicadores, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    executar()
