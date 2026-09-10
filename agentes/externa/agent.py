"""Variante 3 — a ferramenta sai da máquina e chama uma API de verdade.

Na variante `ferramenta` as duas funções só usavam Python. Aqui elas fazem uma
chamada HTTP para a BrasilAPI (<https://brasilapi.com.br>): aberta, sem chave,
sem cadastro.

O CÓDIGO DO AGENTE NÃO MUDA
---------------------------
Compare com `../ferramenta/agent.py`: é a mesma estrutura, as mesmas docstrings,
o mesmo `tools=[...]`. Do ponto de vista do agente, uma função que soma dois
números e uma função que atravessa a internet são a mesma coisa. Isso é bom
(simplicidade) e é perigoso (o modelo não sabe que aquilo custa rede).

O QUE MUDA É TUDO O QUE PODE DAR ERRADO
---------------------------------------
Uma função local falha de um jeito: exceção. Uma função que sai da máquina
falha de muitos: timeout, 403, 500, DNS, resposta com formato diferente do
esperado. Repare que as duas funções abaixo **devolvem `{"erro": ...}` em vez
de estourar**. Ferramenta que levanta exceção derruba o turno inteiro do
agente; ferramenta que devolve erro deixa o modelo explicar o problema para a
pessoa.

    ⚠ A BrasilAPI responde 403 para o User-Agent padrão do urllib. Toda API
    externa tem uma regra dessas. Ver CABECALHOS abaixo.

A PONTE COM O RESTO DO CURSO
----------------------------
`~/bentoml-roberta/api/` usa **a mesma API** para outra coisa: lá os feriados
viram prosa e um modelo de QA extrativo grifa a resposta dentro do texto. Aqui
o agente **chama** a API e lê o JSON. Mesma fonte, dois jeitos de consumir, e
custos de erro bem diferentes — vale abrir os dois lado a lado.
"""

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
