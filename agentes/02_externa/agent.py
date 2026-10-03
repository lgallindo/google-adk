"""02_externa — a ferramenta atravessa a internet.

As funções desta pasta fazem HTTP na BrasilAPI
(<https://brasilapi.com.br>): aberta, sem chave, sem cadastro. Do ponto de
vista do agente, a forma é a mesma de `01_ferramenta` — docstring, tipos,
`tools=[...]`. O que muda é o mundo: timeout, 403, 500, DNS, JSON inesperado.

Por isso cada ferramenta devolve `{"erro": ...}` quando a rede falha. O turno
segue; o modelo explica o problema em português. A BrasilAPI responde 403 ao
User-Agent padrão do `urllib` — os cabeçalhos no código são parte da lição.

Mesma API aparece em `~/bentoml-roberta/api/` como prosa para um modelo de QA.
Aqui o agente lê o JSON. Duas arquiteturas, uma fonte.

    just web            # escolha 02_externa
    just cli 02_externa"""

import json
import urllib.error
import urllib.request
from datetime import date

from google.adk.agents import Agent

from modelo import modelo

TIMEOUT_S = 10
CABECALHOS = {"User-Agent": "agentes-cesar/1.0 (material didatico)"}


def _get(url: str) -> dict | list:
    """Faz o GET e devolve o JSON já decodificado. Levanta em caso de falha."""
    pedido = urllib.request.Request(url, headers=CABECALHOS)
    with urllib.request.urlopen(pedido, timeout=TIMEOUT_S) as resposta:
        return json.load(resposta)


def feriados_do_ano(ano: int) -> dict:
    """Lista os feriados nacionais brasileiros de um ano.

    Args:
        ano: o ano com quatro dígitos, por exemplo 2026.
    """
    try:
        dados = _get(f"https://brasilapi.com.br/api/feriados/v1/{ano}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as erro:
        return {"erro": f"não consegui consultar os feriados de {ano}: {erro}"}

    return {
        "ano": ano,
        "quantidade": len(dados),
        "feriados": [{"data": f["date"], "nome": f["name"]} for f in dados],
    }


def proximo_feriado() -> dict:
    """Diz qual é o próximo feriado nacional e quantos dias faltam para ele."""
    hoje = date.today()
    try:
        dados = _get(f"https://brasilapi.com.br/api/feriados/v1/{hoje.year}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as erro:
        return {"erro": f"não consegui consultar os feriados: {erro}"}

    futuros = [f for f in dados if date.fromisoformat(f["date"]) > hoje]
    if not futuros:
        return {"aviso": f"não há mais feriados nacionais em {hoje.year}"}

    prox = min(futuros, key=lambda f: f["date"])
    return {
        "nome": prox["name"],
        "data": prox["date"],
        "dia_da_semana": prox["weekday"],
        "faltam_dias": (date.fromisoformat(prox["date"]) - hoje).days,
    }


def consultar_cep(cep: str) -> dict:
    """Descobre o endereço de um CEP brasileiro.

    Args:
        cep: o CEP com 8 dígitos, com ou sem hífen, por exemplo "50030-230".
    """
    limpo = "".join(c for c in cep if c.isdigit())
    if len(limpo) != 8:
        return {"erro": f"'{cep}' não tem 8 dígitos"}

    try:
        return _get(f"https://brasilapi.com.br/api/cep/v2/{limpo}")
    except urllib.error.HTTPError as erro:
        if erro.code == 404:
            return {"erro": f"o CEP {cep} não existe"}
        return {"erro": f"a consulta falhou: HTTP {erro.code}"}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as erro:
        return {"erro": f"não consegui consultar o CEP: {erro}"}


root_agent = Agent(
    name="externa",
    model=modelo(),
    description="Consulta feriados nacionais e CEPs na BrasilAPI.",
    instruction=(
        "Você responde sobre feriados nacionais brasileiros e sobre endereços "
        "de CEP, e faz isso SEMPRE consultando as ferramentas. "
        "Você não tem essa informação de cabeça: os feriados mudam de ano para "
        "ano e você não sabe que dia é hoje. Nunca responda de memória. "
        "Se a ferramenta devolver um campo 'erro', explique o erro para a "
        "pessoa em uma frase, em português, e não invente um substituto."
    ),
    tools=[feriados_do_ano, proximo_feriado, consultar_cep],
)
