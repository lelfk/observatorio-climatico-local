from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from coleta import (
    ROOT,
    carregar_configuracao,
    caminhos_dos_dados,
    validar_configuracao,
)

CAMPOS_API = {
    "temperature_2m_min": "temperatura_min_c",
    "temperature_2m_max": "temperatura_max_c",
    "precipitation_sum": "precipitacao_mm",
}


def transformar_e_validar(
    resposta: dict[str, Any],
    config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    validar_configuracao(config)

    diario = resposta.get("daily")
    if not isinstance(diario, dict):
        raise ValueError("O JSON não contém o objeto 'daily'.")

    campos_necessarios = ["time", *CAMPOS_API]
    if any(not isinstance(diario.get(campo), list) for campo in campos_necessarios):
        raise ValueError("Uma ou mais séries diárias estão ausentes.")

    quantidade_esperada = 30
    if any(len(diario[campo]) != quantidade_esperada for campo in campos_necessarios):
        raise ValueError("As séries não contêm exatamente 30 registros.")

    datas = pd.to_datetime(
        pd.Series(diario["time"]),
        format="%Y-%m-%d",
        errors="raise",
    )
    periodo_esperado = pd.date_range(
        start=config["inicio"],
        end=config["fim"],
        freq="D",
    )

    if datas.isna().any():
        raise ValueError("A série contém datas ausentes.")
    if datas.duplicated().any():
        raise ValueError("A série contém datas duplicadas.")
    if list(datas) != list(periodo_esperado):
        raise ValueError("As datas não correspondem ao período configurado.")

    unidades = resposta.get("daily_units")
    if not isinstance(unidades, dict):
        raise ValueError("A resposta não contém unidades diárias válidas.")
    for campo in ("temperature_2m_min", "temperature_2m_max"):
        if unidades.get(campo) not in ("°C", "C"):
            raise ValueError(f"Unidade de temperatura inválida: {campo}.")
    if unidades.get("precipitation_sum") != "mm":
        raise ValueError("A precipitação deve estar expressa em milímetros.")

    if resposta.get("timezone") != config["timezone"]:
        raise ValueError("O fuso horário retornado pela API é diferente do configurado.")

    for campo in CAMPOS_API:
        if any(isinstance(valor, (str, bool, dict, list)) for valor in diario[campo] if valor is not None):
            raise ValueError(f"A série {campo} contém tipos inválidos.")

    dados = pd.DataFrame(
        {campo: diario[campo] for campo in campos_necessarios}
    ).rename(columns={"time": "data", **CAMPOS_API})
    dados["data"] = datas.dt.date

    quantidade_nulos: dict[str, int] = {}
    for campo in CAMPOS_API.values():
        valores_originais = dados[campo].copy()
        dados[campo] = pd.to_numeric(valores_originais, errors="coerce")

        conversoes_invalidas = valores_originais.notna() & dados[campo].isna()
        if conversoes_invalidas.any():
            raise ValueError(f"Há valores não numéricos na coluna {campo}.")

        valores_validos = dados[campo].dropna()
        if not all(math.isfinite(float(valor)) for valor in valores_validos):
            raise ValueError(f"Há valores infinitos na coluna {campo}.")

        quantidade_nulos[campo] = int(dados[campo].isna().sum())

    minima = dados["temperatura_min_c"]
    maxima = dados["temperatura_max_c"]
    precipitacao = dados["precipitacao_mm"]

    if (minima > maxima).fillna(False).any():
        raise ValueError("Há dias em que a temperatura mínima supera a máxima.")
    if (precipitacao < 0).fillna(False).any():
        raise ValueError("A precipitação não pode apresentar valores negativos.")

    for campo in ("temperatura_min_c", "temperatura_max_c"):
        fora_da_faixa = (dados[campo] < -60) | (dados[campo] > 65)
        if fora_da_faixa.fillna(False).any():
            raise ValueError(f"Há valores fora da faixa de controle em {campo}.")

    dados["localidade"] = config["localidade"]
    dados["latitude"] = float(config["latitude"])
    dados["longitude"] = float(config["longitude"])

    colunas = [
        "data",
        "localidade",
        "latitude",
        "longitude",
        "temperatura_min_c",
        "temperatura_max_c",
        "precipitacao_mm",
    ]
    dados = dados[colunas]

    qualidade = {
        "registros": len(dados),
        "inicio": str(dados["data"].min()),
        "fim": str(dados["data"].max()),
        "datas_duplicadas": int(dados["data"].duplicated().sum()),
        "dias_faltantes": 0,
        "cobertura_temporal_pct": 100,
        "nulos": quantidade_nulos,
        "inconsistencias": 0,
        "decisao_sobre_nulos": "Valores ausentes preservados como NULL.",
    }
    return dados, qualidade


def salvar_dados_tratados(
    dados: pd.DataFrame,
    qualidade: dict[str, Any],
) -> None:
    pasta_dados = ROOT / "dados"
    pasta_dados.mkdir(parents=True, exist_ok=True)

    dados.to_csv(
        pasta_dados / "clima_diario_tratado.csv",
        index=False,
        encoding="utf-8",
    )
    (pasta_dados / "qualidade.json").write_text(
        json.dumps(qualidade, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def carregar_no_duckdb(dados: pd.DataFrame) -> int:
    import duckdb

    caminho_banco = ROOT / "dados" / "observatorio.duckdb"

    with duckdb.connect(str(caminho_banco)) as conexao:
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS clima_diario (
                data DATE PRIMARY KEY,
                localidade VARCHAR NOT NULL,
                latitude DOUBLE NOT NULL,
                longitude DOUBLE NOT NULL,
                temperatura_min_c DOUBLE,
                temperatura_max_c DOUBLE,
                precipitacao_mm DOUBLE
            )
            """
        )

        conexao.register("dados_entrada", dados)
        conexao.execute(
            """
            INSERT INTO clima_diario
            SELECT
                data::DATE,
                localidade,
                latitude,
                longitude,
                temperatura_min_c,
                temperatura_max_c,
                precipitacao_mm
            FROM dados_entrada
            ON CONFLICT (data) DO UPDATE SET
                localidade = EXCLUDED.localidade,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                temperatura_min_c = EXCLUDED.temperatura_min_c,
                temperatura_max_c = EXCLUDED.temperatura_max_c,
                precipitacao_mm = EXCLUDED.precipitacao_mm
            """
        )

        quantidade = conexao.execute(
            "SELECT COUNT(*) FROM clima_diario"
        ).fetchone()[0]

    if quantidade != len(dados):
        raise RuntimeError(
            f"Esperados {len(dados)} registros únicos; encontrados {quantidade}."
        )

    return quantidade


def executar() -> None:
    config = carregar_configuracao()
    validar_configuracao(config)

    caminho_json, caminho_metadados = caminhos_dos_dados(config)
    if not caminho_json.exists():
        raise FileNotFoundError("Arquivo original ausente. Execute coleta.py primeiro.")

    if not caminho_metadados.exists():
        raise FileNotFoundError("Metadados da coleta ausentes. Execute coleta.py primeiro.")
    metadados = json.loads(caminho_metadados.read_text(encoding="utf-8"))
    if hashlib.sha256(caminho_json.read_bytes()).hexdigest() != metadados.get("sha256"):
        raise ValueError("Falha de integridade: hash SHA-256 do JSON original divergente ou ausente.")

    resposta = json.loads(caminho_json.read_text(encoding="utf-8"))
    dados, qualidade = transformar_e_validar(resposta, config)

    salvar_dados_tratados(dados, qualidade)
    quantidade = carregar_no_duckdb(dados)

    print(f"Validação concluída: {qualidade}")
    print(f"DuckDB atualizado: {quantidade} registros únicos.")


if __name__ == "__main__":
    executar()
