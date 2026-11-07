"""Gera relatório técnico de três páginas, figuras e evidências a partir do DuckDB real."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
import duckdb
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Image, PageBreak, Spacer, KeepTogether
)
from coleta import ROOT, configuracao, arquivos

def executar():
    cfg = configuracao()
    original, meta_path = arquivos(cfg)
    db_path = ROOT / "dados" / "observatorio.duckdb"
    qualidade_path = ROOT / "dados" / "qualidade.json"
    for p in (original, meta_path, db_path, qualidade_path):
        if not p.exists():
            raise FileNotFoundError(f"Evidência real ausente: {p}. Execute coleta.py e banco.py.")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    qualidade = json.loads(qualidade_path.read_text(encoding="utf-8"))
    with duckdb.connect(str(db_path), read_only=True) as db:
        tabela = db.execute("SELECT * FROM clima_diario ORDER BY data").df()
        if len(tabela) != 30 or tabela["data"].duplicated().any():
            raise ValueError("Banco não contém 30 datas únicas")
        texto = (ROOT / "consultas.sql").read_text(encoding="utf-8")
        consultas = [s.strip() for s in texto.split(";") if s.strip()]
        if len(consultas) != 3:
            raise ValueError("Exatamente três consultas SQL são obrigatórias.")
        resultado = [db.execute(sql).df() for sql in consultas]
    if len(resultado[0]) == 0:
        raise ValueError("Sem dados válidos de temperatura máxima; não produzir relatório numérico.")
    num = lambda x: "não disponível" if x is None or pd.isna(x) else f"{float(x):.1f}".replace(".", ",")
    maior = float(resultado[0]["maior_temperatura_c"].iloc[0])
    datas_max = [str(d)[:10] for d in resultado[0]["data"].tolist()]
    chuva = resultado[1].iloc[0]
    termica = resultado[2].iloc[0]
    dias_chuva = int(chuva["dias_com_chuva"])
    dias_precip = int(chuva["dias_com_dado"])
    dias_validos = int(termica["dias_validos"])
    saida = ROOT / "dados" / "evidencias"
    saida.mkdir(parents=True, exist_ok=True)
    indicadores = {
        "fonte": "Open-Meteo Historical Weather API", "localidade": cfg["localidade"],
        "periodo": [cfg["inicio"], cfg["fim"]],
        "maior_temperatura_maxima_c": maior, "datas_maior_maxima": datas_max,
        "precipitacao_total_mm": None if pd.isna(chuva["precipitacao_total_mm"]) else float(chuva["precipitacao_total_mm"]),
        "dias_com_chuva": dias_chuva, "dias_com_dado_precipitacao": dias_precip,
        "temperatura_media_aproximada_c": None if pd.isna(termica["temperatura_media_aproximada_c"]) else float(termica["temperatura_media_aproximada_c"]),
        "dias_termicos_validos": dias_validos, "amplitude_termica_media_c": None if pd.isna(termica["amplitude_termica_media_c"]) else float(termica["amplitude_termica_media_c"]),
    }
    (ROOT / "dados" / "indicadores.json").write_text(
        json.dumps(indicadores, ensure_ascii=False, indent=2), encoding="utf-8")
    consultas_txt = []
    for i, res in enumerate(resultado, start=1):
        consultas_txt.append(f"CONSULTA {i}\n{res.to_string(index=False)}\n")
    (saida / "consultas_sql.txt").write_text("\n".join(consultas_txt), encoding="utf-8")
    tabela.head(6).to_csv(saida / "amostra_banco.csv", index=False)
    dias = pd.to_datetime(tabela["data"])
    labels = dias.dt.strftime("%d/%m")
    plt.rcParams.update({"font.size": 9})
    fig, ax = plt.subplots(figsize=(8.4, 2.15), dpi=145)
    ax.plot(dias, tabela["temperatura_min_c"], label="Temperatura mínima", linewidth=1.7)
    ax.plot(dias, tabela["temperatura_max_c"], label="Temperatura máxima", linewidth=1.7)
    ax.set_ylabel("°C"); ax.grid(alpha=0.2)
    ax.legend(loc="upper left", fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()
    temperatura_img = saida / "temperaturas.png"
    fig.savefig(temperatura_img); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8.4, 2.15), dpi=145)
    ax.bar(dias, tabela["precipitacao_mm"], width=0.7)
    ax.set_ylabel("mm"); ax.grid(axis="y", alpha=0.2)
    fig.autofmt_xdate()
    fig.tight_layout()
    chuva_img = saida / "precipitacao.png"
    fig.savefig(chuva_img); plt.close(fig)

    pdf_dir = ROOT / "docs" / "escopo-1" / "AE2"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf = pdf_dir / "Relatorio_AE2_Observatorio_Climatico.pdf"
    doc = SimpleDocTemplate(str(pdf), pagesize=(21*cm, 29.7*cm),
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=1.8*cm, bottomMargin=1.7*cm,
                            title="AE2 - Observatório Climático Local - Ipiranga")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TituloA", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=16,
                              leading=20, textColor=colors.HexColor("#12334A"), spaceAfter=13))
    styles.add(ParagraphStyle(name="SubA", parent=styles["Heading2"], fontSize=10.5,
                              leading=14, textColor=colors.HexColor("#087E85"), spaceBefore=8, spaceAfter=7))
    styles.add(ParagraphStyle(name="TextoA", parent=styles["Normal"], fontSize=8.7,
                              leading=12.8, alignment=TA_JUSTIFY, spaceAfter=8))
    styles.add(ParagraphStyle(name="NotaA", parent=styles["Normal"], fontSize=7.6, leading=10.7,
                              textColor=colors.HexColor("#566675"), spaceAfter=7))
    sty = []
    def P(s, name="TextoA"): sty.append(Paragraph(s, styles[name]))
    def H(s): P(s, "SubA")
    def T(rows, widths):
        tab = Table(rows, colWidths=widths, hAlign="LEFT", repeatRows=1)
        tab.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,0),colors.HexColor("#12334A")),
            ("TEXTCOLOR", (0,0),(-1,0),colors.white),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#EEF4F6")]),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("FONTSIZE",(0,0),(-1,-1),7.6),
            ("BOTTOMPADDING",(0,0),(-1,-1),7),
            ("TOPPADDING",(0,0),(-1,-1),7),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ]))
        sty.append(tab)
    P("OBSERVATÓRIO CLIMÁTICO LOCAL<br/>AE2 | Relatório técnico e analítico", "TituloA")
    H("1. Contexto, necessidade e continuidade")
    P("Este projeto organiza registros meteorológicos históricos do Ipiranga, São Paulo/SP, para apoiar a comunidade escolar do território, especialmente estudantes e educadores, na compreensão das oscilações de temperatura e precipitação. O material pode apoiar atividades didáticas sobre episódios passados de chuva e calor, incluindo reflexões sobre atividades ao ar livre. A necessidade concreta e a utilidade da apresentação ainda precisam ser verificadas com representantes desse público.")
    P("<b>Planejamento e continuidade:</b> a apresentação e a transcrição da Aula 1 do Projeto Integrador Extensionista 2 orientam o escopo e o caráter comunitário. Não foi localizado registro individual prévio da AE1; localidade, público e perguntas são definidos e documentados neste projeto. O Projeto Integrador 1 citado na aula corresponde a uma disciplina anterior, apresentada pelo docente apenas como retrospectiva.")
    H("2. Recorte, questões e indicadores")
    P(f"<b>Localidade:</b> {cfg['localidade']} (latitude {cfg['latitude']}, longitude {cfg['longitude']}). "
      f"<b>Período:</b> {cfg['inicio']} a {cfg['fim']}, 30 dias consecutivos. "
      f"<b>Fuso:</b> {cfg['timezone']}. <b>Variáveis:</b> temperaturas mínima/máxima diárias (°C) e precipitação diária acumulada (mm).")
    P("Perguntas: (1) qual foi a temperatura máxima mais alta e quando ocorreu? "
      "(2) quanto choveu no período e em quantos dias houve chuva? "
      "(3) qual foi a temperatura média diária aproximada? Indicadores principais: maior máxima (°C), "
      "precipitação acumulada (mm) e média das semissomas diárias das temperaturas mínima e máxima (°C).")
    H("3. Fonte e coleta de dados")
    P("Os dados foram obtidos pela <b>Open-Meteo Historical Weather API</b>, "
      "https://archive-api.open-meteo.com/v1/archive, por requisição GET no Python com a biblioteca Requests, "
      "informando coordenadas, datas, variáveis e fuso. A resposta original em JSON foi preservada sem alteração "
      "e teve seu SHA-256 registrado em arquivo de metadados.")
    P(f"<b>Evidência:</b> coleta em UTC {meta.get('coletado_em_utc', 'não informado')}, "
      f"HTTP {meta.get('status_http', 'não informado')}; URL integral em <i>dados/originais</i>; "
      f"SHA-256 {meta.get('sha256','')[:24]}…")
    sty.append(PageBreak())

    P("Tratamento, armazenamento e evidências", "TituloA")
    H("4. Tratamento e controle de qualidade")
    P("O pandas organizou as variáveis, converteu datas e tipos numéricos, conferiu unidades, "
      "comparou os 30 dias esperados com as datas retornadas e rejeitou duplicidades e inconsistências "
      "(temperatura mínima acima da máxima, chuva negativa ou temperaturas fora da faixa de verificação). "
      "Valores ausentes foram preservados como NULL, nunca substituídos por zero sem justificativa.")
    P(f"<b>Resultado:</b> {qualidade['registros']} registros; cobertura temporal "
      f"{qualidade['cobertura_temporal_pct']}%; datas duplicadas: {qualidade['datas_duplicadas']}; "
      f"datas faltantes: {qualidade['dias_faltantes']}; ausências por variável: "
      f"{qualidade['nulos']}.")
    H("5. Estrutura e carga DuckDB")
    P("A tabela <b>clima_diario</b> contém data DATE (chave primária), localidade VARCHAR, "
      "latitude e longitude DOUBLE, temperatura_min_c DOUBLE, temperatura_max_c DOUBLE e precipitacao_mm DOUBLE. "
      "A carga usa INSERT ... ON CONFLICT(data) DO UPDATE, impedindo duplicações em reexecuções.")
    T([["Data", "Mín. (°C)", "Máx. (°C)", "Chuva (mm)"]] +
      [[str(r["data"])[:10],num(r["temperatura_min_c"]),num(r["temperatura_max_c"]),num(r["precipitacao_mm"])]
       for _,r in tabela.head(4).iterrows()], [4.1*cm, 4*cm, 4*cm, 4.9*cm])
    H("6. Séries históricas")
    sty.append(Image(str(temperatura_img), width=16.4*cm, height=4.2*cm))
    sty.append(Spacer(1, 0.2*cm))
    sty.append(Image(str(chuva_img), width=16.4*cm, height=4.2*cm))
    P("Gráficos derivados dos registros consultados e carregados no DuckDB. Não são medições diretas de uma estação instalada no distrito.", "NotaA")
    sty.append(PageBreak())

    P("Análise e aplicação extensionista", "TituloA")
    H("7. Consultas SQL e resultados")
    T([["KPI / consulta", "Resultado", "Unidade"]] +
      [["Maior temperatura máxima",num(maior) + " (" + ", ".join(datas_max) + ")","°C"],
       ["Precipitação acumulada",num(chuva["precipitacao_total_mm"]),"mm"],
       ["Temperatura média aproximada",num(termica["temperatura_media_aproximada_c"]),"°C"]],
      [7.7*cm, 7*cm, 2.3*cm])
    P(f"A <b>primeira consulta</b> selecionou MAX(temperatura_max_c) e a(s) data(s) correspondente(s): "
      f"{num(maior)} °C em {', '.join(datas_max)}. A <b>segunda</b> somou os valores de chuva: "
      f"{num(chuva['precipitacao_total_mm'])} mm, com precipitação em {dias_chuva} dias "
      f"e {dias_precip} registros válidos. A <b>terceira</b> calculou AVG((mínima+máxima)/2): "
      f"{num(termica['temperatura_media_aproximada_c'])} °C em {dias_validos} dias completos; "
      f"a amplitude térmica média foi {num(termica['amplitude_termica_media_c'])} °C. "
      "As instruções estão disponíveis integralmente em <b>consultas.sql</b>, "
      "e seus resultados tabulares em <b>dados/evidencias/consultas_sql.txt</b>.")
    H("8. Critérios de sucesso e interpretação")
    P("Os critérios técnicos verificados incluem 30 registros únicos, cobertura integral, unidades coerentes, "
      "validação de ausências e inconsistências, três consultas SQL, três indicadores e dois gráficos produzidos. "
      "A coleta automatizada no GitHub Actions retornou HTTP 200 e preservou o JSON de origem, permitindo reprodução. "
      "A média das semissomas de mínimas e máximas é aproximada e não corresponde à média horária observada.")
    H("9. Relevância extensionista, ética e limites")
    P("Os dias de maior calor e precipitação podem ser usados por docentes em atividades retrospectivas "
      "sobre condições meteorológicas e planejamento escolar. A Aula 1 recomenda ouvir representantes "
      "do público, sempre que possível, para validar a necessidade e evitar pressuposições. "
      "Esse contato e a devolutiva ainda não foram realizados; nenhuma entrevista ou avaliação de impacto é atribuída ao projeto. "
      "Não são coletados dados pessoais nesta etapa; eventual feedback deverá respeitar finalidade e privacidade.")
    P("A Open-Meteo fornece séries meteorológicas baseadas em modelos/reanálise para um ponto geográfico; "
      "não há comprovação de que os valores sejam observações de estação no Ipiranga. "
      "Um intervalo de 30 dias não permite inferir tendências climáticas multianuais, "
      "e esta análise histórica não constitui previsão meteorológica.")
    H("10. Fontes e reprodutibilidade")
    P("Open-Meteo: https://open-meteo.com/en/docs/historical-weather-api. "
      "DuckDB: https://duckdb.org/docs/stable/. "
      "Orientação didática: transcrição da Aula 1, Projeto Integrador Extensionista 2 "
      "(material disponibilizado pelo estudante; síntese em docs/escopo-1/AE2). "
      "Código, README, JSON original, SQL e evidências: "
      "https://github.com/lelfk/observatorio-climatico-local.")
    def pagina(canvas, documento):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#C9D9E2"))
        canvas.line(2*cm, 1.35*cm, 19*cm, 1.35*cm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#556979"))
        canvas.drawString(2*cm, 1.05*cm, "Observatório Climático Local | Projeto Integrador Extensionista 2")
        canvas.drawRightString(19*cm, 1.05*cm, f"Página {documento.page}")
        canvas.restoreState()
    doc.build(sty, onFirstPage=pagina, onLaterPages=pagina)
    print("RELATÓRIO GERADO:", pdf)
    print("KPIs:", json.dumps(indicadores, ensure_ascii=False))

if __name__ == "__main__":
    executar()
