from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parent
API_URL = "https://archive-api.open-meteo.com/v1/archive"
VARIAVEIS_ESPERADAS = {
    "temperature_2m_min",
    "temperature_2m_max",
    "precipitation_sum",
}


def carregar_configuracao() -> dict[str, Any]:
    caminho = ROOT / "config.json"
    return json.loads(caminho.read_text(encoding="utf-8"))


def validar_configuracao(config: dict[str, Any]) -> None:
    obrigatorios = {
        "localidade",
        "latitude",
        "longitude",
        "inicio",
        "fim",
        "timezone",
        "variaveis",
    }
    ausentes = obrigatorios - set(config.keys())
    if ausentes:
        raise ValueError(f"Campos ausentes em config.json: {sorted(ausentes)}")

    inicio = date.fromisoformat(config["inicio"])
    fim = date.fromisoformat(config["fim"])

    if (fim - inicio).days + 1 != 30:
        raise ValueError("O periodo deve conter 30 dias consecutivos.")
    if fim >= date.today():
        raise ValueError("A data final deve ser anterior à data atual.")

    if set(config["variaveis"]) != VARIAVEIS_ESPERADAS:
        raise ValueError("Configure exatamente as três variáveis previstas no projeto.")

    latitude = float(config["latitude"])
    longitude = float(config["longitude"])
    if not -90 <= latitude <= 90:
        raise ValueError("Latitude deve estar entre -90 e 90.")
    if not -180 <= longitude <= 180:
        raise ValueError("Longitude deve estar entre -180 e 180.")
    if not config["timezone"]:
        raise ValueError("Informe o fuso horário da localidade.")


def caminhos_dos_dados(config: dict[str, Any]) -> tuple[Path, Path]:
    pasta = ROOT / "dados" / "originais"
    nome = f"open_meteo_{config['inicio']}_{config['fim']}"
    return pasta / f"{nome}.json", pasta / f"{nome}_metadados.json"


def criar_sessao() -> requests.Session:
    tentativas = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    sessao = requests.Session()
    sessao.mount("https://", HTTPAdapter(max_retries=tentativas))
    return sessao


def coletar_dados(
    config: dict[str, Any],
) -> tuple[bytes, dict[str, Any], str, dict[str, Any], int]:
    parametros = {
        "latitude": config["latitude"],
        "longitude": config["longitude"],
        "start_date": config["inicio"],
        "end_date": config["fim"],
        "daily": ",".join(config["variaveis"]),
        "timezone": config["timezone"],
        "temperature_unit": "celsius",
        "precipitation_unit": "mm",
    }

    resposta = criar_sessao().get(
        API_URL,
        params=parametros,
        timeout=(15, 80),
        headers={"User-Agent": "Observatorio-Climatico-Local/1.0"},
    )
    resposta.raise_for_status()

    try:
        dados = resposta.json()
    except Exception as erro:
        raise ValueError(f"A resposta da API nao e um JSON valido: {erro}") from erro

    metadados = {
        "url": resposta.url,
        "status_code": resposta.status_code,
        "headers": dict(resposta.headers),
        "coletado_em": datetime.now(timezone.utc).isoformat(),
        "parametros": parametros,
    }

    tamanho = len(resposta.content)
    return resposta.content, dados, resposta.url, metadados, tamanho


def salvar_dados_originais(
    conteudo_bruto: bytes, metadados: dict[str, Any], config: dict[str, Any]
) -> tuple[Path, Path]:
    caminho_bruto, caminho_metadados = caminhos_dos_dados(config)
    caminho_bruto.parent.mkdir(parents=True, exist_ok=True)

    caminho_bruto.write_bytes(conteudo_bruto)
    caminho_metadados.write_text(
        json.dumps(metadados, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return caminho_bruto, caminho_metadados


def executar() -> tuple[Path, Path]:
    config = carregar_configuracao()
    validar_configuracao(config)
    conteudo_bruto, _, _, metadados, _ = coletar_dados(config)
    return salvar_dados_originais(conteudo_bruto, metadados, config)


if __name__ == "__main__":
    executar()
