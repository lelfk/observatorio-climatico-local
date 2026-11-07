"""Converte, valida e persiste em DuckDB; repetição da carga não duplica datas."""
from __future__ import annotations
import json
from pathlib import Path

import pandas as pd
from coleta import ROOT, arquivos, configuracao, conferir_config

CAMPOS = {
    "temperature_2m_min": "temperatura_min_c",
    "temperature_2m_max": "temperatura_max_c",
    "precipitation_sum": "precipitacao_mm",
}

def transformar_validar(payload, cfg):
    conferir_config(cfg)
    diario = payload.get("daily")
    if not isinstance(diario, dict):
        raise ValueError("JSON sem objeto daily")
    campos = ["time", *CAMPOS]
    if any(not isinstance(diario.get(c), list) for c in campos):
        raise ValueError("Datas ou variável diária ausente")
    if any(len(diario[c]) != 30 for c in campos):
        raise ValueError("A API não retornou os 30 registros esperados")
    datas = pd.to_datetime(pd.Series(diario["time"]), format="%Y-%m-%d", errors="raise")
    esperado = pd.date_range(cfg["inicio"], cfg["fim"], freq="D")
    if datas.isna().any() or datas.duplicated().any() or list(datas) != list(esperado):
        raise ValueError("Datas duplicadas, fora de ordem ou ausentes")
    unidades = payload.get("daily_units", {})
    if any(unidades.get(c) not in ("°C", "C") for c in list(CAMPOS)[:2]):
        raise ValueError("Unidade de temperatura não é Celsius")
    if unidades.get("precipitation_sum") != "mm":
        raise ValueError("Unidade de precipitação não é mm")
    if payload.get("timezone") and payload["timezone"] != cfg["timezone"]:
        raise ValueError("Fuso horário da API diferente do configurado")

    df = pd.DataFrame({c: diario[c] for c in campos}).rename(columns={"time": "data", **CAMPOS})
    df["data"] = datas.dt.date
    nulos = {}
    for campo in CAMPOS.values():
        bruto = df[campo].copy()
        df[campo] = pd.to_numeric(bruto, errors="coerce")
        if (bruto.notna() & df[campo].isna()).any():
            raise ValueError(f"Valor inválido não numérico: {campo}")
        nulos[campo] = int(df[campo].isna().sum())
    if (df["temperatura_min_c"] > df["temperatura_max_c"]).fillna(False).any():
        raise ValueError("Temperatura mínima superior à máxima")
    if (df["precipitacao_mm"] < 0).fillna(False).any():
        raise ValueError("Precipitação negativa")
    for campo in ("temperatura_min_c", "temperatura_max_c"):
        if ((df[campo] < -60) | (df[campo] > 65)).fillna(False).any():
            raise ValueError("Temperatura fora da faixa de controle; revisar fonte")
    df["localidade"] = cfg["localidade"]
    df["latitude"] = float(cfg["latitude"])
    df["longitude"] = float(cfg["longitude"])
    df = df[["data", "localidade", "latitude", "longitude",
             "temperatura_min_c", "temperatura_max_c", "precipitacao_mm"]]
    qualidade = {
        "registros": len(df), "inicio": str(df["data"].min()), "fim": str(df["data"].max()),
        "datas_duplicadas": int(df["data"].duplicated().sum()),
        "dias_faltantes": 0, "cobertura_temporal_pct": 100,
        "nulos": nulos, "inconsistencias": 0,
        "decisao_sobre_nulos": "Preservados como NULL; não substituir por zero.",
    }
    return df, qualidade

def executar():
    import duckdb
    cfg = configuracao()
    origem, _ = arquivos(cfg)
    if not origem.exists():
        raise FileNotFoundError("JSON original não encontrado; execute coleta.py")
    df, qualidade = transformar_validar(json.loads(origem.read_text(encoding="utf-8")), cfg)
    dados = ROOT / "dados"
    dados.mkdir(parents=True, exist_ok=True)
    df.to_csv(dados / "clima_diario_tratado.csv", index=False, encoding="utf-8")
    (dados / "qualidade.json").write_text(json.dumps(qualidade, indent=2, ensure_ascii=False), encoding="utf-8")
    with duckdb.connect(str(dados / "observatorio.duckdb")) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS clima_diario (
                data DATE PRIMARY KEY, localidade VARCHAR NOT NULL,
                latitude DOUBLE NOT NULL, longitude DOUBLE NOT NULL,
                temperatura_min_c DOUBLE, temperatura_max_c DOUBLE, precipitacao_mm DOUBLE
            )
        """)
        con.register("entrada", df)
        con.execute("""
            INSERT INTO clima_diario
            SELECT data::DATE, localidade, latitude, longitude,
                   temperatura_min_c, temperatura_max_c, precipitacao_mm FROM entrada
            ON CONFLICT(data) DO UPDATE SET
                localidade=EXCLUDED.localidade, latitude=EXCLUDED.latitude,
                longitude=EXCLUDED.longitude,
                temperatura_min_c=EXCLUDED.temperatura_min_c,
                temperatura_max_c=EXCLUDED.temperatura_max_c,
                precipitacao_mm=EXCLUDED.precipitacao_mm
        """)
        qtd = con.execute("SELECT COUNT(*) FROM clima_diario").fetchone()[0]
        if qtd != 30:
            raise RuntimeError(f"Esperado 30 registros únicos, obtido {qtd}")
    print("VALIDAÇÃO OK:", qualidade)
    print("DUCKDB OK: 30 registros únicos (carga idempotente)")

if __name__ == "__main__":
    executar()
