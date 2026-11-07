"""Consulta a API histórica da Open-Meteo e preserva os bytes do JSON original."""
from __future__ import annotations
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parent
API = "https://archive-api.open-meteo.com/v1/archive"

def configuracao():
    return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

def conferir_config(cfg):
    inicio, fim = date.fromisoformat(cfg["inicio"]), date.fromisoformat(cfg["fim"])
    if (fim - inicio).days + 1 != 30:
        raise ValueError("O recorte precisa conter 30 dias consecutivos.")
    esperado = {"temperature_2m_min", "temperature_2m_max", "precipitation_sum"}
    if set(cfg["variaveis"]) != esperado or len(cfg["variaveis"]) != 3:
        raise ValueError("As variáveis configuradas não correspondem ao recorte de três variáveis.")
    if fim >= date.today():
        raise ValueError("A data final deve ser anterior à data atual.")

def arquivos(cfg):
    p = ROOT / "dados" / "originais"
    nome = f"open_meteo_{cfg['inicio']}_{cfg['fim']}"
    return p / (nome + ".json"), p / (nome + "_metadados.json")

def executar():
    cfg = configuracao()
    conferir_config(cfg)
    params = {
        "latitude": cfg["latitude"], "longitude": cfg["longitude"],
        "start_date": cfg["inicio"], "end_date": cfg["fim"],
        "daily": ",".join(cfg["variaveis"]), "timezone": cfg["timezone"],
        "temperature_unit": "celsius", "precipitation_unit": "mm",
    }
    sessao = requests.Session()
    repeticao = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    sessao.mount("https://", HTTPAdapter(max_retries=repeticao))
    resposta = sessao.get(API, params=params, timeout=(15, 80),
                        headers={"User-Agent": "Observatorio-Climatico-Local-Academico/1.0"})
    resposta.raise_for_status()
    payload = resposta.json()
    if payload.get("error") or not isinstance(payload.get("daily"), dict):
        raise RuntimeError(f"Resposta inesperada da API: {payload.get('reason', 'sem dados diarios')}")
    destino, meta = arquivos(cfg)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(".json.tmp")
    temporario.write_bytes(resposta.content)
    temporario.replace(destino)
    registro = {
        "fonte": "Open-Meteo Historical Weather API",
        "endpoint": API, "url": resposta.url,
        "parametros": params, "coletado_em_utc": datetime.now(timezone.utc).isoformat(),
        "status_http": resposta.status_code, "arquivo": str(destino.relative_to(ROOT)),
        "sha256": hashlib.sha256(resposta.content).hexdigest(),
        "natureza": "Dados históricos modelados/reanálise, não medições diretas de estação local.",
    }
    meta.write_text(json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8")
    print("COLETA OK:", len(payload["daily"].get("time", [])), "dias |", resposta.url)

if __name__ == "__main__":
    executar()
