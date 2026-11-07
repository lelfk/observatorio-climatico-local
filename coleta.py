"""Coleta dados meteorológicos históricos da Open-Meteo."""

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
    """Lê as definições do projeto no arquivo config.json."""
    caminho = ROOT / "config.json"
    return json.loads(caminho.read_text(encoding="utf-8"))


def validar_configuracao(config: dict[str, Any]) -> None:
    """Confere os campos e o intervalo definidos para a coleta."""
    obrigatorios = {
        "localidade",
        "latitude",
        "longitude",
        "inicio",
        "fim",
        "timezone",
        "variaveis",
    }
    ausentes = obrigatorios.difference(config)
    if ausentes:
        raise ValueError(f"Campos ausentes em config.json: {sorted(ausentes)}")

    inicio = date.fromisoformat(config["inicio"])
    fim = date.fromisoformat(config["fim"])

    if (fim - inicio).days + 1 != 30:
        raise ValueError("O período deve conter 30 dias consecutivos.")
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
    """Retorna os caminhos do JSON original e de seus metadados."""
    pasta = ROOT / "dados" / "originais"
    nome = f"open_meteo_{config['inicio']}_{config['fim']}"
    return pasta / f"{nome}.json", pasta / f"{nome}_metadados.json"


def criar_sessao() -> requests.Session:
    """Configura tentativas automáticas para falhas temporárias da API."""
    tentativas = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    sessao = requests.Session()
    sessao.mount("https://", HTTPAdapter(max_retries=tentativas))
    return sessao


def coletar_dados(config: dict[str, Any]) -> tuple[bytes, dict[str, Any], str]:
    """Consulta a API e retorna a resposta original, o JSON e a URL."""
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
    except requests.exceptions.JSONDecodeError as erro:
        raise ValueError("A API não retornou um JSON válido.") from erro

    if dados.get("error") or not isinstance(dados.get("daily"), dict):
        motivo = dados.get("reason", "estrutura diária ausente")
        raise ValueError(f"Resposta inesperada da Open-Meteo: {motivo}")

    datas = dados["daily"].get("time", [])
    if len(datas) != 30:
        raise ValueError(f"Esperados 30 dias; a API retornou {len(datas)}.")

    return resposta.content, dados, resposta.url


def salvar_dados_originais(
    conteudo: bytes,
    url: str,
    parametros: dict[str, Any],
    status_http: int,
    config: dict[str, Any],
) -> None:
    """Salva a resposta original e metadados para permitir auditoria."""
    caminho_json, caminho_metadados = caminhos_dos_dados(config)
    caminho_json.parent.mkdir(parents=True, exist_ok=True)

    temporario = caminho_json.with_suffix(".json.tmp")
    temporario.write_bytes(conteudo)
    temporario.replace(caminho_json)

    metadados = {
        "fonte": "Open-Meteo Historical Weather API",
        "endpoint": API_URL,
        "url": url,
        "parametros": parametros,
        "coletado_em_utc": datetime.now(timezone.utc).isoformat(),
        "status_http": status_http,
        "arquivo": str(caminho_json.relative_to(ROOT)),
        "sha256": hashlib.sha256(conteudo).hexdigest(),
        "natureza": (
            "Dados históricos baseados em modelos e/ou reanálise; "
            "não representam necessariamente medições de uma estação local."
        ),
    }
    caminho_metadados.write_text(
        json.dumps(metadados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def executar() -> None:
    """Executa a coleta e registra a resposta da API."""
    config = carregar_configuracao()
    validar_configuracao(config)

    conteudo, dados, url = coletar_dados(config)
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

    salvar_dados_originais(
        conteudo=conteudo,
        url=url,
        parametros=parametros,
        status_http=200,
        config=config,
    )
    print(f"Coleta concluída: {len(dados['daily']['time'])} dias.")
    print(f"Fonte: {url}")


if __name__ == "__main__":
    executar()
