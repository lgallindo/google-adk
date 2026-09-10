import json
import urllib.request

from google.adk.agents import Agent

from .modelo import modelo

SERVICO = "http://localhost:3000/risco"


def risco_de_recurso(orgao: str, decisao: str) -> dict:
    """Estima o risco de um pedido da LAI virar recurso.

    Args:
        orgao: nome do órgão destinatário, por exemplo "Ministério da Saúde".
        decisao: a decisão dada ao pedido, por exemplo "Acesso Negado".
    """
    corpo = json.dumps({"OrgaoDestinatario": orgao, "Decisao": decisao}).encode()
    pedido = urllib.request.Request(
        SERVICO, corpo, {"Content-Type": "application/json"}
    )
    return json.load(urllib.request.urlopen(pedido))


def orcamento_de_revisao(pedidos_na_fila: int, percentual: float) -> dict:
    """Quantos pedidos a ouvidoria consegue revisar antes de responder.

    Args:
        pedidos_na_fila: quantos pedidos estão na fila.
        percentual: fatia da fila que dá para revisar, de 0 a 100.
    """
    return {"pode_revisar": int(pedidos_na_fila * percentual / 100)}


root_agent = Agent(
    name="triagem",
    model=modelo(),
    description="Ajuda a ouvidoria a escolher quais pedidos da LAI revisar.",
    instruction=(
        "Você ajuda a ouvidoria a decidir quais pedidos revisar antes de responder. "
        "Use risco_de_recurso para consultar o modelo e orcamento_de_revisao para "
        "saber quantos pedidos cabem na revisão. Explique o número em uma frase; "
        "nunca invente um risco sem chamar a ferramenta."
    ),
    tools=[risco_de_recurso, orcamento_de_revisao],
)
