"""Variante 5 — o mesmo "em ordem" do `debate`, escrito como `Workflow`.

POR QUE ESTA PASTA EXISTE
-------------------------
`SequentialAgent`, `LoopAgent` e `ParallelAgent` estão **deprecados** no ADK
2.8: importar qualquer um dos três já imprime um aviso dizendo que serão
removidos "in favor of Workflow". As variantes `debate`, `ata` e `paralelo`
continuam funcionando, e continuam sendo a forma mais fácil de explicar
orquestração — mas o substituto oficial é este.

A MUDANÇA DE CABEÇA: DE ÁRVORE PARA GRAFO
-----------------------------------------
`SequentialAgent` é uma ÁRVORE: um agente-casca com uma lista `sub_agents`, e
a ordem é a ordem da lista.

    SequentialAgent(sub_agents=[rascunho, revisor])

`Workflow` é um GRAFO: você não declara uma lista, declara as ARESTAS, e a
ordem é consequência de quem aponta para quem.

    Workflow(edges=[(START, rascunho, revisor)])

Essa tupla é um atalho para uma CORRENTE: ela vira duas arestas,
`START -> rascunho` e `rascunho -> revisor`. `START` é o nó de entrada; ele
nunca executa, só marca por onde o grafo começa.

Em linha reta os dois desenhos dão no mesmo. A diferença aparece quando o
caminho não é reto: num grafo você escreve `{"aprovado": fim, "refazer":
rascunho}` e tem desvio e volta atrás, coisas que `sub_agents=[...]` não sabe
dizer.

⚠ UM `Workflow` NÃO É UM AGENTE
-------------------------------
`LlmAgent` herda de `BaseAgent`; `Workflow` herda de `BaseNode`. São hierarquias
diferentes, e isso tem duas consequências práticas:

1. A relação só vale num sentido. Um agente pode ser nó de um workflow (é o que
   acontece aqui). Um workflow **ainda não** pode ser `sub_agent` de um
   `LlmAgent` — o próprio aviso de deprecação diz isso.
2. `App`/`Runner` aceitam os dois como raiz (`root_agent: BaseAgent | BaseNode`),
   então o `adk web` serve esta pasta como serve as outras.

COMO OS DOIS NÓS CONVERSAM
--------------------------
Do mesmo jeito do `debate`, e de propósito: `output_key` grava a resposta numa
chave do estado, e a instrução do nó seguinte interpola `{essa_chave}`. O grafo
manda na ORDEM; quem carrega o CONTEÚDO continua sendo o estado da sessão.

    just web            # http://localhost:8000, escolha "fluxo"
    just cli fluxo
"""

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
