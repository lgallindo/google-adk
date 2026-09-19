"""Variante 5c — só a primeira metade do `pesquisa`: abre em três e fecha.

A variante `pesquisa` tem onze chamadas ao modelo e sete papéis diferentes.
Ela mostra um pipeline de verdade, e é grande demais para ser a primeira coisa
que alguém lê sobre grafos. Esta pasta é o mesmo desenho cortado no primeiro
fechamento: quatro chamadas, dois conceitos, nada mais.

    START → esboco ─┬→ fontes_1 ─┐
                    ├→ fontes_2 ─┼→ fontes_prontas → relator
                    └→ fontes_3 ─┘

    5 chamadas ao modelo: 1 esboço + 3 pesquisadores em paralelo + 1 relator.

A rampa das variantes de grafo fica assim:

    fluxo      2 nós em fila          a SINTAXE do Workflow
    fontes     abre em 3 e costura    fan-out, fan-in e relatório  ← aqui
    pesquisa   sete papéis, 11 nós    um pipeline inteiro

O QUE ESTA PASTA ENSINA, E É SÓ ISSO
------------------------------------
**Fan-out é uma tupla.** Dentro da corrente, uma tupla no lugar de um nó abre o
leque: o ADK dispara os três ao mesmo tempo, cada um no seu ramo.

    (esboco, (fontes_1, fontes_2, fontes_3), fontes_prontas)

**Fan-in é um `JoinNode`.** E esta é a parte que não se adivinha. Um nó COMUM
que recebe três arestas de entrada **não espera as três**: cada predecessor que
termina enfileira um gatilho próprio, então o nó roda TRÊS VEZES, a primeira
assim que o pesquisador mais rápido acaba. O `JoinNode` declara
`_requires_all_predecessors`, e o orquestrador troca o gatilho por uma BARREIRA,
que só libera quando os três chegaram.

Troque `fontes_prontas` por um `Agent` qualquer e o bug aparece — mas não como
erro: como texto escrito com um terço da bibliografia, num terminal limpo. É por
isso que a barreira ganhou uma pasta só para ela.

BARREIRA NÃO ESCREVE; QUEM ESCREVE É O `relator`
------------------------------------------------
Vale saber o que a barreira entrega, porque não é um texto. `JoinNode` REPASSA
o que recebeu, num dicionário com uma entrada por predecessor:

    {"fontes_1": ..., "fontes_2": ..., "fontes_3": ...}

Se o grafo terminasse ali, a execução acabaria nesse dicionário: no `adk web`
você veria as três bibliografias como três mensagens (cada pesquisador
respondeu no ramo dele) e o fim, sem nenhum parágrafo costurando as três.

Por isso existe o `relator`, depois da barreira. E repare COMO ele lê: não é o
dicionário da barreira que chega nele — ele interpola `{esbocos}`,
`{fontes_1}`, `{fontes_2}` e `{fontes_3}` do estado da sessão, como qualquer
agente das outras variantes. A barreira garante o QUANDO (os três terminaram);
o estado carrega o QUE.

O `relator` RELATA, e não desenvolve: ele organiza num documento o que já foi
escrito, sem transformar esboço em projeto. Quem desenvolve é o `redator` do
`pesquisa`, que é o passo seguinte da rampa.

> Como as outras pastas de aula, esta se sustenta sozinha: os prompts são uma
> cópia enxugada do `pesquisa`, e não um import. O `adk` carrega cada variante
> como módulo de primeiro nível, e uma pasta que depende da vizinha quebra a
> aula quando a vizinha muda.

    just web            # http://localhost:8000, escolha "fontes"
    just cli fontes
"""

from google.adk.agents import Agent
from google.adk.workflow import START, JoinNode, Workflow

from modelo import modelo

QUANTAS = 3

esboco = Agent(
    name="esboco",
    model=modelo(),
    description="Gera três propostas de pesquisa a partir de um tema.",
    instruction=(
        "A pessoa vai te dar um TEMA de pesquisa. "
        f"Proponha exatamente {QUANTAS} propostas de pesquisa distintas sobre "
        "esse tema, numeradas de 1 a 3, um PARÁGRAFO cada.\n\n"
        "Cada parágrafo precisa deixar claro a pergunta de pesquisa, o que "
        "seria investigado e por que isso importa. As três têm que ser mesmo "
        "diferentes entre si, e não três formas de dizer a mesma coisa.\n\n"
        "Use exatamente este formato, porque os pesquisadores contam com ele:\n"
        "## Proposta 1\n<parágrafo>\n## Proposta 2\n<parágrafo>\n"
        "## Proposta 3\n<parágrafo>\n\n"
        "Não escreva nada antes nem depois."
    ),
    output_key="esbocos",
)


def criar_pesquisador(i: int) -> Agent:
    """O pesquisador da proposta `i`.

    Uma fábrica, e não três blocos copiados, porque a única diferença entre
    eles é o NÚMERO da proposta. Cada chamada devolve um agente novo, com nome
    e `output_key` próprios: dois nós do grafo não podem ter o mesmo nome, e
    duas chaves de estado iguais se sobrescreveriam.
    """
    return Agent(
        name=f"fontes_{i}",
        model=modelo(),
        description=f"Levanta bibliografia comentada da proposta {i}.",
        instruction=(
            "Estas são as propostas que foram esboçadas:\n\n"
            "{esbocos}\n\n"
            f"Trabalhe APENAS na Proposta {i}. Ignore as outras duas: elas têm "
            "outros pesquisadores, e você não sabe o que eles vão escrever — "
            "quando você começou, eles também estavam começando.\n\n"
            "Entregue duas coisas:\n\n"
            "**Bibliografia comentada** — de 5 a 6 trabalhos relevantes. Para "
            "cada um: referência (autores, título, veículo, ano) e DUAS frases "
            "dizendo o que o trabalho mostra e por que importa para esta "
            "proposta.\n\n"
            "**Fichamentos** — os 2 trabalhos mais centrais, um fichamento "
            "cada: problema atacado, método, resultado principal e a lacuna "
            "que ele deixa aberta.\n\n"
            "⚠ Você está trabalhando de memória, sem buscar em base nenhuma. "
            "Marque com [VERIFICAR] toda referência de que você não tenha "
            "certeza. Quatro referências marcadas valem mais que seis "
            "inventadas com cara de certas."
        ),
        output_key=f"fontes_{i}",
    )


pesquisadores = [criar_pesquisador(i) for i in range(1, QUANTAS + 1)]

# A barreira. Não chama modelo, não escreve nada: só espera os três.
fontes_prontas = JoinNode(name="fontes_prontas")

relator = Agent(
    name="relator",
    model=modelo(),
    description="Relata num documento único o esboço e a bibliografia das três.",
    instruction=(
        "Monte o relatório desta rodada de levantamento. Você tem tudo:\n\n"
        "ESBOÇOS DAS PROPOSTAS:\n{esbocos}\n\n"
        "BIBLIOGRAFIA DA PROPOSTA 1:\n{fontes_1}\n\n"
        "BIBLIOGRAFIA DA PROPOSTA 2:\n{fontes_2}\n\n"
        "BIBLIOGRAFIA DA PROPOSTA 3:\n{fontes_3}\n\n"
        "Escreva UM documento em Markdown, nesta estrutura:\n\n"
        "# Levantamento de propostas de pesquisa\n\n"
        "## Sumário\n"
        "Uma tabela com uma linha por proposta e as colunas: Nº, Assunto em "
        "poucas palavras, Quantas referências, Quantas marcadas [VERIFICAR].\n\n"
        "## Proposta N — <assunto>\n"
        "Para cada uma das três, nesta ordem: o esboço como ele foi escrito, a "
        "bibliografia comentada e os fichamentos.\n\n"
        "## Referências a verificar\n"
        "Lista de toda referência marcada com [VERIFICAR], dizendo em qual "
        "proposta ela aparece. Se não houver nenhuma, diga isso "
        "explicitamente.\n\n"
        "## O que este levantamento ainda não responde\n"
        "Três a cinco linhas: o que falta saber antes de escolher uma das "
        "propostas para desenvolver.\n\n"
        "Você RELATA, não desenvolve: não transforme esboço em projeto, não "
        "acrescente método que ninguém escreveu e não invente referência que "
        "não esteja acima. "
        "Preserve as marcas [VERIFICAR] — não limpe o que o pesquisador marcou "
        "como incerto. "
        "Também não escolha a melhor proposta: esta rodada é de levantamento, e "
        "a escolha é de quem lê."
    ),
    output_key="relatorio",
)

# A tupla abre o leque; o JoinNode fecha; o relator costura. O grafo é esta linha.
root_agent = Workflow(
    name="fontes",
    description=(
        "Esboça três propostas, levanta a bibliografia das três em paralelo e "
        "relata tudo num documento."
    ),
    edges=[(START, esboco, tuple(pesquisadores), fontes_prontas, relator)],
)
