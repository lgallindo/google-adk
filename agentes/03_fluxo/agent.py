"""03_fluxo — dois nós em fila, escritos como grafo.

Nesta pasta a orquestração vira `Workflow`: você declara arestas, e a ordem
é consequência de quem aponta para quem.

    Workflow(edges=[(START, rascunho, revisor)])

A tupla é uma corrente: `START → rascunho → revisor`. `START` só marca a
entrada. Em linha reta o resultado parece uma fila; a forma de grafo abre
desvios e voltas quando o caminho deixa de ser reto
(`{"aprovado": fim, "refazer": rascunho}`).

Os nós conversam pelo estado da sessão: `output_key` grava a resposta; o
próximo interpola `{essa_chave}` na instrução. O grafo manda no quando; o
estado carrega o quê.

`Workflow` herda de `BaseNode` (e `LlmAgent` de `BaseAgent`). Um agente pode
ser nó de um workflow; o `adk web` aceita os dois como raiz.

    just web            # escolha 03_fluxo
    just cli 03_fluxo"""

from google.adk.agents import Agent
from google.adk.workflow import START, Workflow

from modelo import modelo

rascunho = Agent(
    name="rascunho",
    model=modelo(),
    description="Escreve a primeira versão, sem se preocupar em polir.",
    instruction=(
        "Escreva um primeiro rascunho curto do que a pessoa pediu: "
        "NO MÁXIMO quatro frases. "
        "É rascunho, então prefira estar completo a estar bonito. "
        "Não peça desculpa pelo texto e não comente o que você fez."
    ),
    output_key="rascunho",
)

revisor = Agent(
    name="revisor",
    model=modelo(),
    description="Corta o que sobra do rascunho e entrega a versão final.",
    instruction=(
        "Este é o rascunho que o colega escreveu:\n\n"
        "{rascunho}\n\n"
        "Reescreva-o mais curto e mais claro, no MÁXIMO três frases, "
        "mantendo todos os fatos. "
        "Depois acrescente uma última linha começando com 'Cortei: ' "
        "dizendo em poucas palavras o que você tirou e por quê."
    ),
    output_key="final",
)

# As arestas do grafo. A tupla é uma corrente: START -> rascunho -> revisor.
root_agent = Workflow(
    name="fluxo",
    description="Rascunho e revisão em ordem, orquestrados por grafo.",
    edges=[(START, rascunho, revisor)],
)
