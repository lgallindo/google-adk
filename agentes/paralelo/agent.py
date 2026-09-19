"""Variante 4c — três pareceres ao mesmo tempo, sobre um pedido de LAI real.

A variante `debate` põe três agentes em FILA: o cético lê o que a otimista
escreveu, o pragmático lê os dois. Aqui a fila some. Os três rodam JUNTOS,
sobre um pedido de verdade da base da CGU (`dados/`, 60 pedidos de 2025).

    SequentialAgent "paralelo"
    ├── LlmAgent "porteiro"            busca o pedido -> state["pedido"]
    ├── ParallelAgent "pareceres"      ← os três ao mesmo tempo
    │   ├── LlmAgent "juridico"   -> state["parecer_juridico"]
    │   ├── LlmAgent "merito"     -> state["parecer_merito"]
    │   └── LlmAgent "risco"      -> state["parecer_risco"]
    └── LlmAgent "relator"             lê os três e fecha

Cinco chamadas ao modelo: 1 porteiro + 3 pareceres + 1 relator.

A UMA IDEIA NOVA: ELES NÃO SE ESCUTAM
-------------------------------------
No `debate`, cada agente interpola `{arg_otimista}` na instrução e lê a fala
do colega. Aqui isso é IMPOSSÍVEL, e não é limitação do ADK: é aritmética. Os
três começam no mesmo instante, então quando o jurídico monta o prompt dele o
parecer de mérito ainda não existe. Não há o que ler.

Repare no que eles CONSEGUEM ler: `{pedido}`, que o porteiro escreveu ANTES
do bloco paralelo. Estado escrito antes de o bloco começar todo mundo enxerga;
estado escrito dentro do bloco, ninguém. A fronteira é o instante da largada.

Troca-se conversa por tempo. Use `ParallelAgent` quando as partes forem mesmo
independentes (três ângulos do mesmo texto, três fontes, três traduções) e
`SequentialAgent` quando uma precisar da anterior.

O RELATOR É QUEM COSTURA
------------------------
O `ParallelAgent` não resume nada — ele dispara e espera. Quem junta é o
agente seguinte na sequência, lendo as três chaves de estado. Por isso o
`root_agent` é um `SequentialAgent`. Esse par fan-out/fan-in é o desenho
padrão, e é o motivo de `ParallelAgent` quase nunca aparecer sozinho.

O GABARITO EXISTE E O MODELO NÃO O VÊ
-------------------------------------
Cada pedido da amostra sabe se a pessoa recorreu de verdade. O parecerista de
`risco` tem que adivinhar isso sem ver. Depois, no terminal:

    just gabarito 50001121584202581

Metade da amostra virou recurso, então chutar "sim" para tudo acerta 50%. É
esse o piso contra o qual o parecer de risco tem que ser comparado.

⚠ PARALELO NÃO É SEMPRE MAIS RÁPIDO
-----------------------------------
`ParallelAgent` paraleliza a ESPERA, não a CONTA. Com o Gemini as três
chamadas viajam pela rede ao mesmo tempo e o bloco custa o tempo do parecer
mais lento, não a soma dos três. Com o Qwen3 local não: `servico-qwen/` é um
processo só, gerando token a token na CPU, então as três chegam juntas e são
atendidas uma de cada vez. Meça em vez de acreditar:

    just cronometro                      # Gemini (padrão) — ganho de verdade
    ADK_BACKEND=qwen3 just cronometro    # Qwen local — linha reta, sem ganho

⚠ DEPRECIADO NA 2.8.0
---------------------
Rodar isto imprime um aviso:

    DeprecationWarning: ParallelAgent is deprecated in favor of Workflow
    and will be removed in a future version.

Vale para `SequentialAgent` e `LoopAgent` também — os três viraram legado na
2.x em favor do `Workflow`, que é um grafo (`from google.adk import Workflow`,
com uma lista de `edges`). Nada quebra, mas é honesto dizer em sala: isto é o
jeito clássico, não o jeito novo.
"""

from google.adk.agents import Agent, ParallelAgent, SequentialAgent

from modelo import modelo
from paralelo.pedidos import FERRAMENTAS

REGRA_COMUM = (
    "Você analisa UM pedido de acesso à informação já respondido pelo órgão. "
    "O pedido está em {pedido?}. "
    "Escreva NO MÁXIMO quatro frases, no seu ângulo e só nele. "
    "Dois colegas analisam o mesmo pedido neste instante, por outros ângulos: "
    "você não sabe o que eles vão dizer, então não cite, não responda e não "
    "suponha a opinião deles. "
    "Cite trechos do pedido ou da resposta quando eles sustentarem o que você "
    "está dizendo. Não invente artigo de lei, número nem data."
)


def criar_pareceristas() -> list[Agent]:
    """Os três pareceristas, sempre novos.

    É uma função, e não três variáveis soltas, porque um agente só pode ter
    UM pai: se você pendurar o mesmo objeto num `ParallelAgent` e num
    `SequentialAgent`, o ADK reclama. O `cronometro.py` precisa exatamente
    disso — os mesmos três montados de dois jeitos — então cada chamada
    devolve um trio novinho.
    """
    juridico = Agent(
        name="juridico",
        model=modelo(),
        description="Confere se a decisão do órgão se sustenta na LAI.",
        instruction=(
            "Você é a parecerista jurídica. Pergunte se a decisão do órgão se "
            "sustenta na Lei 12.527/2011: se houve negativa ou restrição, o "
            "órgão indicou fundamento legal e prazo de sigilo? O fundamento "
            "citado cobre mesmo o que foi pedido, ou é genérico? Se a decisão "
            "foi de concessão, diga se ela foi formalmente completa. "
            "Aponte UM defeito jurídico concreto, ou diga que não achou. "
            + REGRA_COMUM
        ),
        output_key="parecer_juridico",
    )

    merito = Agent(
        name="merito",
        model=modelo(),
        description="Confere se a resposta responde o que foi perguntado.",
        instruction=(
            "Você é o parecerista de mérito. Ignore se a decisão é legal: "
            "pergunte se a resposta RESPONDE. Liste o que a pessoa pediu, "
            "item por item, e marque o que o órgão entregou, o que ele "
            "ignorou e o que ele respondeu com evasiva ou com link genérico. "
            "Seja específico sobre o que ficou sem resposta. " + REGRA_COMUM
        ),
        output_key="parecer_merito",
    )

    risco = Agent(
        name="risco",
        model=modelo(),
        description="Prevê se a pessoa vai recorrer da resposta.",
        instruction=(
            "Você é a parecerista de risco. Preveja se esta pessoa vai entrar "
            "com recurso contra a resposta. Termine com uma linha exatamente "
            "neste formato:\n"
            "RISCO: alto|médio|baixo — <a razão, em até dez palavras>\n"
            "Pese o tom de insistência de quem pediu, se a resposta devolve "
            "menos do que foi perguntado, e se a negativa veio sem "
            "fundamento claro. Na base de onde veio esta amostra, metade dos "
            "pedidos virou recurso: se você responder 'alto' para tudo, você "
            "acerta 50% e não serviu para nada. " + REGRA_COMUM
        ),
        output_key="parecer_risco",
    )

    return [juridico, merito, risco]


porteiro = Agent(
    name="porteiro",
    model=modelo(),
    description="Acha o pedido na amostra e o coloca na mesa.",
    instruction=(
        "Você abre a análise. A pessoa vai pedir um protocolo específico, um "
        "pedido de um tipo de decisão, ou um pedido qualquer.\n"
        "- Protocolo citado: chame buscar_pedido.\n"
        "- 'um negado', 'um parcial', 'qualquer um': chame sortear_pedido.\n"
        "- Pergunta sobre a amostra em si: chame resumo_da_amostra.\n\n"
        "Depois de receber o pedido, reescreva-o INTEIRO e sem resumir, "
        "porque três pareceristas vão ler só o que você escrever aqui, e "
        "cortar texto agora vira parecer errado depois. Use este formato:\n\n"
        "PROTOCOLO: ...\nÓRGÃO: ...\nDATA: ...\nASSUNTO: ...\n"
        "DECISÃO: ... (especificação, se houver)\n"
        "MOTIVO DA NEGATIVA: ... (ou 'não se aplica')\n\n"
        "--- O QUE FOI PEDIDO ---\n<texto integral>\n\n"
        "--- O QUE O ÓRGÃO RESPONDEU ---\n<texto integral>\n\n"
        "Não comente, não opine e não analise: isso é trabalho dos outros."
    ),
    tools=FERRAMENTAS,
    output_key="pedido",
)

pareceres = ParallelAgent(
    name="pareceres",
    description="Jurídico, mérito e risco — os três ao mesmo tempo.",
    sub_agents=criar_pareceristas(),
)

relator = Agent(
    name="relator",
    model=modelo(),
    description="Junta os três pareceres numa recomendação só.",
    instruction=(
        "Três pareceristas analisaram o mesmo pedido de acesso à informação "
        "em paralelo, sem conversar entre si:\n"
        "- jurídico (a decisão se sustenta na LAI?): {parecer_juridico?}\n"
        "- mérito (a resposta responde?): {parecer_merito?}\n"
        "- risco (a pessoa vai recorrer?): {parecer_risco?}\n\n"
        "Escreva em quatro partes, nesta ordem:\n"
        "1. **O pedido** — órgão, o que foi pedido e o que foi decidido, "
        "em uma frase.\n"
        "2. **Onde eles concordam** — em uma frase.\n"
        "3. **Onde eles se contradizem** — o conflito real entre dois "
        "pareceres e qual dos dois você segue. Repare que 'a negativa é "
        "legal' e 'a resposta não responde' NÃO se contradizem: os dois "
        "podem ser verdade ao mesmo tempo. Se não houver contradição de "
        "verdade, diga isso em vez de inventar uma.\n"
        "4. **Recomendação** — manter a resposta, complementar, ou reformar, "
        "e uma única ação concreta para a ouvidoria.\n\n"
        "Você não sabe se houve recurso de verdade: não finja que sabe. "
        "Não invente parecer que ninguém deu."
    ),
)

root_agent = SequentialAgent(
    name="paralelo",
    description=(
        "Busca um pedido de LAI real, manda três pareceristas analisarem ao "
        "mesmo tempo e costura o resultado."
    ),
    sub_agents=[porteiro, pareceres, relator],
)
