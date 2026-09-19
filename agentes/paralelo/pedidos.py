"""Acesso à amostra de pedidos da LAI, e as ferramentas que o agente usa.

O arquivo de dados é `dados/pedidos.jsonl` — 60 pedidos reais de 2025, da base
do FalaBR da CGU. Veja `dados/README.md` para a procedência e
`dados/baixar.py` para regerar.

A REGRA DO GABARITO
-------------------
Cada pedido guarda `houve_recurso`: se a pessoa recorreu de verdade. Nenhuma
função deste arquivo que o modelo possa chamar devolve esse campo —
`_sem_gabarito()` remove antes de entregar. O gabarito sai só por
`conferir_gabarito()`, que é para a turma rodar DEPOIS, no terminal, e não
está na lista de ferramentas de nenhum agente.

Se o modelo pudesse ler o gabarito, o parecer de risco deixaria de ser uma
previsão e viraria uma consulta. É o erro mais comum em demonstração de
agente: dar ao modelo a resposta e se impressionar quando ele acerta.
"""

from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path

ARQUIVO = Path(__file__).resolve().parent / "dados" / "pedidos.jsonl"

CAMPOS_GABARITO = ("houve_recurso", "qtd_recursos")


@lru_cache(maxsize=1)
def carregar() -> tuple[dict, ...]:
    """Lê o JSONL inteiro, gabarito incluído. Uso interno e do terminal."""
    if not ARQUIVO.exists():
        raise FileNotFoundError(
            f"Não achei {ARQUIVO}.\n"
            "Rode:  just dados   (baixa da CGU e regera a amostra)"
        )
    with open(ARQUIVO, encoding="utf-8") as f:
        return tuple(json.loads(linha) for linha in f if linha.strip())


def _sem_gabarito(pedido: dict) -> dict:
    return {k: v for k, v in pedido.items() if k not in CAMPOS_GABARITO}


# --- ferramentas do agente ---------------------------------------------------


def buscar_pedido(protocolo: str) -> dict:
    """Busca um pedido de acesso à informação pelo número de protocolo.

    Args:
        protocolo: O número do protocolo, com ou sem pontuação. Ex.:
            "50001121584202581".

    Returns:
        O pedido com o texto da solicitação, a resposta do órgão e a decisão,
        ou um erro se o protocolo não estiver na amostra.
    """
    limpo = "".join(c for c in protocolo if c.isdigit())
    for pedido in carregar():
        if pedido["protocolo"] == limpo:
            return _sem_gabarito(pedido)
    return {
        "erro": f"Protocolo {protocolo} não está na amostra.",
        "dica": "Use sortear_pedido para pegar um pedido qualquer.",
    }


def sortear_pedido(decisao: str = "") -> dict:
    """Sorteia um pedido da amostra, opcionalmente filtrando pela decisão.

    Args:
        decisao: Opcional. Um de "Acesso Concedido", "Acesso Negado",
            "Acesso Parcialmente Concedido", "Informação Inexistente".
            Vazio sorteia entre todos.

    Returns:
        Um pedido sorteado, com solicitação, resposta e decisão.
    """
    candidatos = [
        p for p in carregar()
        if not decisao or p["decisao"].lower() == decisao.strip().lower()
    ]
    if not candidatos:
        return {
            "erro": f"Nenhum pedido com decisão {decisao!r}.",
            "decisoes_disponiveis": sorted({p["decisao"] for p in carregar()}),
        }
    return _sem_gabarito(random.choice(candidatos))


def resumo_da_amostra() -> dict:
    """Conta quantos pedidos há na amostra, por decisão e por órgão.

    Returns:
        Totais da amostra, para situar antes de escolher um pedido.
    """
    todos = carregar()
    por_decisao: dict[str, int] = {}
    por_orgao: dict[str, int] = {}
    for pedido in todos:
        por_decisao[pedido["decisao"]] = por_decisao.get(pedido["decisao"], 0) + 1
        por_orgao[pedido["orgao"]] = por_orgao.get(pedido["orgao"], 0) + 1
    maiores = sorted(por_orgao.items(), key=lambda kv: -kv[1])[:10]
    return {
        "total": len(todos),
        "por_decisao": por_decisao,
        "orgaos_mais_frequentes": dict(maiores),
        "orgaos_distintos": len(por_orgao),
    }


FERRAMENTAS = [buscar_pedido, sortear_pedido, resumo_da_amostra]


# --- só para o terminal, nunca para o modelo ---------------------------------


def conferir_gabarito(protocolo: str) -> dict:
    """O que aconteceu de verdade com esse pedido. NÃO é ferramenta de agente."""
    limpo = "".join(c for c in protocolo if c.isdigit())
    for pedido in carregar():
        if pedido["protocolo"] == limpo:
            return {
                "protocolo": pedido["protocolo"],
                "orgao": pedido["orgao"],
                "decisao": pedido["decisao"],
                "houve_recurso": pedido["houve_recurso"],
                "qtd_recursos": pedido["qtd_recursos"],
            }
    return {"erro": f"Protocolo {protocolo} não está na amostra."}


def listar(decisao: str = "") -> None:
    """Imprime a amostra inteira, com gabarito. Cola de professor.

    É a lista de onde você tira os protocolos para usar em aula. Como ela
    mostra o gabarito, não projete na tela antes do exercício.
    """
    filtrados = [
        p for p in carregar()
        if not decisao or decisao.lower() in p["decisao"].lower()
    ]
    print(f"\n{len(filtrados)} pedidos" + (f" com decisão ~{decisao!r}" if decisao else ""))
    print(f"\n{'PROTOCOLO':<20} {'RECURSO':<8} {'DECISÃO':<32} ÓRGÃO")
    print("-" * 100)
    for p in filtrados:
        marca = "SIM" if p["houve_recurso"] else "não"
        print(f"{p['protocolo']:<20} {marca:<8} {p['decisao'][:30]:<32} {p['orgao'][:38]}")
    com = sum(1 for p in filtrados if p["houve_recurso"])
    print(f"\n{com} viraram recurso, {len(filtrados) - com} não.")
    print("Ver um pedido inteiro:  uv run python agentes/paralelo/pedidos.py ver <protocolo>\n")


def ver(protocolo: str) -> None:
    """Imprime um pedido inteiro, como o modelo o recebe (sem gabarito)."""
    pedido = buscar_pedido(protocolo)
    if "erro" in pedido:
        raise SystemExit(pedido["erro"])
    for campo in ("protocolo", "orgao", "data_registro", "assunto", "decisao",
                  "especificacao_decisao", "motivo_negativa"):
        print(f"{campo:<24} {pedido[campo] or '—'}")
    print("\n--- O QUE FOI PEDIDO ---\n" + pedido["pedido"])
    print("\n--- O QUE O ÓRGÃO RESPONDEU ---\n" + pedido["resposta"])
    print("\n(o gabarito não aparece aqui, e nem para o modelo — "
          "use: just gabarito " + pedido["protocolo"] + ")\n")


if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    if not args:
        resumo = resumo_da_amostra()
        print(json.dumps(resumo, ensure_ascii=False, indent=2))
        com = sum(1 for p in carregar() if p["houve_recurso"])
        print(f"\ngabarito: {com} dos {resumo['total']} viraram recurso")
        print("\n  listar todos:  uv run python agentes/paralelo/pedidos.py listar")
        print("  ver um:        uv run python agentes/paralelo/pedidos.py ver <protocolo>")
        print("  gabarito:      uv run python agentes/paralelo/pedidos.py <protocolo>")
    elif args[0] == "listar":
        listar(" ".join(args[1:]))
    elif args[0] == "ver":
        ver(args[1])
    else:
        print(json.dumps(conferir_gabarito(args[0]), ensure_ascii=False, indent=2))
