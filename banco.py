from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from coleta import carregar_configuracao

ROOT = Path(__file__).resolve().parent
CAMINHO_JSON_PADRAO = (
    ROOT / "dados" / "originais" / "open_meteo_2024-09-01_2024-09-30.json"
)
CAMINHO_CSV_TRATADO = ROOT / "dados" / "tratados" / "clima_ipiranga_setembro_2024.csv"
CAMINHO_QUALIDADE = ROOT / "dados" / "tratados" / "qualidade_dados.json"
CAMINHO_DUCKDB = ROOT / "dados" / "clima.duckdb"


def transformar_e_validar(
    caminho_json: Path = CAMINHO_JSON_PADRAO,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    config = carregar_configuracao()
    dados_json = json.loads(caminho_json.read_text(encoding="utf-8"))

    diario = dados_json.get("daily", {})
    datas = diario.get("time", [])
    temp_min = diario.get("temperature_2m_min", [])
    temp_max = diario.get("temperature_2m_max", [])
    precipitacao = diario.get("precipitation_sum", [])

    if not (len(datas) == len(temp_min) == len(temp_max) == len(precipitacao)):
        raise ValueError("Tamanhos de listas inconsistentes no JSON.")

    df = pd.DataFrame(
        {
            "data": pd.to_datetime(datas).date,
            "localidade": config["localidade"],
            "latitude": float(dados_json["latitude"]),
            "longitude": float(dados_json["longitude"]),
            "temperatura_min_c": temp_min,
            "temperatura_max_c": temp_max,
            "precipitacao_mm": precipitacao,
        }
    )

    datas_esperadas = pd.date_range(config["inicio"], config["fim"]).date
    datas_ausentes = sorted(set(datas_esperadas) - set(df["data"]))
    if datas_ausentes:
        raise ValueError(f"Datas ausentes na serie: {datas_ausentes}")

    unidades = dados_json.get("daily_units", {})
    if unidades.get("temperature_2m_min") != "°C":
        raise ValueError("Unidade de temperatura minima invalida.")
    if unidades.get("temperature_2m_max") != "°C":
        raise ValueError("Unidade de temperatura maxima invalida.")
    if unidades.get("precipitation_sum") != "mm":
        raise ValueError("Unidade de precipitacao invalida.")

    if (df["temperatura_min_c"] > df["temperatura_max_c"]).any():
        raise ValueError("Existe registro com temperatura minima maior que a maxima.")
    if (df["precipitacao_mm"] < 0).any():
        raise ValueError("Existe registro com precipitacao negativa.")

    inconsistencias_temp = df[
        (df["temperatura_min_c"] < -10)
        | (df["temperatura_min_c"] > 45)
        | (df["temperatura_max_c"] < -10)
        | (df["temperatura_max_c"] > 45)
    ]
    if not inconsistencias_temp.empty:
        raise ValueError("Valores de temperatura fora dos limites plausiveis.")

    inconsistencias_prec = df[df["precipitacao_mm"] > 300]
    if not inconsistencias_prec.empty:
        raise ValueError("Valores de precipitacao fora dos limites plausiveis.")

    resumo_qualidade = {
        "total_registros": len(df),
        "datas_unicas": df["data"].nunique(),
        "nulos_temp_min": int(df["temperatura_min_c"].isna().sum()),
        "nulos_temp_max": int(df["temperatura_max_c"].isna().sum()),
        "nulos_precipitacao": int(df["precipitacao_mm"].isna().sum()),
        "dias_com_chuva": int((df["precipitacao_mm"] > 0).sum()),
        "precipitacao_total_mm": float(df["precipitacao_mm"].sum()),
    }

    return df, resumo_qualidade


def salvar_dados_tratados(
    df: pd.DataFrame, resumo: dict[str, Any]
) -> tuple[Path, Path]:
    CAMINHO_CSV_TRATADO.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CAMINHO_CSV_TRATADO, index=False)
    CAMINHO_QUALIDADE.write_text(
        json.dumps(resumo, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return CAMINHO_CSV_TRATADO, CAMINHO_QUALIDADE


def salvar_no_duckdb(
    df: pd.DataFrame, caminho_db: Path = CAMINHO_DUCKDB
) -> tuple[Path, int]:
    caminho_db.parent.mkdir(parents=True, exist_ok=True)
    dados = df.copy()

    conexao = duckdb.connect(str(caminho_db))
    try:
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
    finally:
        conexao.close()

    return caminho_db, quantidade


def executar() -> tuple[Path, Path, Path, int]:
    df, resumo = transformar_e_validar()
    csv_path, json_path = salvar_dados_tratados(df, resumo)
    db_path, quantidade = salvar_no_duckdb(df)
    return csv_path, json_path, db_path, quantidade


if __name__ == "__main__":
    executar()
