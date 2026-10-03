"""09_pesquisa — um pipeline de pesquisa em grafo, com dois abre-e-fecha.

Sete papéis, onze nós, onze chamadas ao modelo. O grafo abre em três ramos
duas vezes — fontes e crivo — e fecha cada leque num `JoinNode` antes de
seguir.

    START → esboco → (fontes ×3) → fontes_prontas → redator
          → bibliografia → (crivo ×3) → crivo_pronto → plano → relator

Fan-out é tupla; fan-in é `JoinNode`. Fechar o leque num nó comum faz o
próximo passo rodar cedo, com bibliografia pela metade, sem erro no terminal.
A barreira segura o quando; o estado da sessão carrega o quê.

O filtro do crivo mora na instrução do `plano`: das três propostas, ele
escreve plano só para quem passou. Roteamento por aresta condicional escolhe
um caminho para a execução inteira; aqui a decisão é por item.

Rode uma vez, com tema pequeno, e leia a aba **State** no `adk web`. É pasta
para inspecionar, mais do que para repetir na cota gratuita.

    just web            # escolha 09_pesquisa
    just cli 09_pesquisa"""

from google.adk.agents import Agent
from google.adk.workflow import START, JoinNode, Workflow

from modelo import modelo

QUANTAS = 3

# --- 1. O esboço -------------------------------------------------------------

esboco = Agent(
    name="esboco",
    model=modelo(),
    description="Gera três propostas de pesquisa a partir de um tema.",
    instruction=(
        "A pessoa vai te dar um TEMA de pesquisa. "
        f"Proponha exatamente {QUANTAS} propostas de pesquisa distintas sobre "
        "esse tema, numeradas de 1 a 3, um PARÁGRAFO cada.\n\n"
        "Cada parágrafo precisa deixar claro: a pergunta de pesquisa, o que "
        "seria investigado e por que isso importa. "
        "As três têm que ser mesmo diferentes entre si — ângulos, métodos ou "
        "recortes distintos, não três formas de dizer a mesma coisa.\n\n"
        "Use exatamente este formato, porque os próximos agentes contam com ele:\n"
        "## Proposta 1\n<parágrafo>\n## Proposta 2\n<parágrafo>\n"
        "## Proposta 3\n<parágrafo>\n\n"
        "Não escreva nada antes nem depois. Não comente o que você fez."
    ),
    output_key="esbocos",
)


# --- 2. Os três pesquisadores, em paralelo -----------------------------------


def criar_pesquisador(i: int) -> Agent:
    """O pesquisador da proposta `i`.

    É uma fábrica, e não três blocos copiados, porque a única diferença entre
    eles é o NÚMERO da proposta que cada um pega. Cada chamada devolve um
    agente novo, com nome e `output_key` próprios — dois nós do grafo não podem
    ter o mesmo nome, e duas chaves de estado iguais se sobrescreveriam.
    """
    return Agent(
        name=f"fontes_{i}",
        model=modelo(),
        description=f"Levanta bibliografia comentada da proposta {i}.",
        instruction=(
            "Estas são as propostas de pesquisa que foram esboçadas:\n\n"
            "{esbocos}\n\n"
            f"Trabalhe APENAS na Proposta {i}. Ignore as outras duas: elas têm "
            "outros pesquisadores, e você não sabe o que eles vão escrever.\n\n"
            "Entregue duas coisas, nesta ordem:\n\n"
            "**Bibliografia comentada** — de 4 a 6 trabalhos relevantes. Para "
            "cada um: referência (autores, título, veículo, ano) e DUAS frases "
            "dizendo o que o trabalho mostra e por que ele importa para esta "
            "proposta.\n\n"
            "**Fichamentos** — escolha os 2 trabalhos mais centrais e faça um "
            "fichamento de cada: problema atacado, método usado, resultado "
            "principal, e a lacuna que ele deixa aberta.\n\n"
            "⚠ Você está trabalhando de memória, sem buscar em base nenhuma. "
            "Então marque cada referência de que você não tem certeza com "
            "[VERIFICAR]. É melhor entregar quatro referências marcadas do que "
            "seis inventadas com cara de certas."
        ),
        output_key=f"fontes_{i}",
    )


pesquisadores = [criar_pesquisador(i) for i in range(1, QUANTAS + 1)]

# A barreira. Não chama modelo: só espera os três pesquisadores.
fontes_prontas = JoinNode(name="fontes_prontas")


# --- 3. O redator ------------------------------------------------------------

redator = Agent(
    name="redator",
    model=modelo(),
    description="Transforma os três esboços em projetos de pesquisa.",
    instruction=(
        "Estes são os esboços iniciais:\n\n{esbocos}\n\n"
        "E esta é a bibliografia que os pesquisadores levantaram para cada um:\n\n"
        "### Fontes da Proposta 1\n{fontes_1}\n\n"
        "### Fontes da Proposta 2\n{fontes_2}\n\n"
        "### Fontes da Proposta 3\n{fontes_3}\n\n"
        "Desenvolva cada esboço num PROJETO de pesquisa, usando a bibliografia "
        "da proposta correspondente. Para cada uma das três, escreva:\n\n"
        "## Proposta N — <título>\n"
        "**Problema e justificativa** (um parágrafo, ancorado nas fontes)\n"
        "**Pergunta de pesquisa** (uma frase)\n"
        "**Método** (um parágrafo: dados, procedimento, como se analisa)\n"
        "**Resultado esperado** (uma frase)\n"
        "**Referências** (só as que você de fato citou acima)\n\n"
        "Cite as fontes pelo sobrenome e ano no corpo do texto. "
        "Preserve as marcas [VERIFICAR] que vierem da bibliografia — não limpe "
        "o que o pesquisador marcou como incerto."
    ),
    output_key="propostas",
)


# --- 4. O auditor de bibliografia -------------------------------------------

bibliografia = Agent(
    name="bibliografia",
    model=modelo(),
    description="Audita as referências de cada proposta.",
    instruction=(
        "Estes são os três projetos:\n\n{propostas}\n\n"
        "E esta é a bibliografia original de cada um:\n\n"
        "### Fontes da Proposta 1\n{fontes_1}\n\n"
        "### Fontes da Proposta 2\n{fontes_2}\n\n"
        "### Fontes da Proposta 3\n{fontes_3}\n\n"
        "Audite a bibliografia de cada proposta, uma por uma. Para cada:\n\n"
        "- **Citado mas ausente**: referência citada no corpo que não está na "
        "lista de referências.\n"
        "- **Listado mas não usado**: referência na lista que não é citada em "
        "lugar nenhum.\n"
        "- **Suspeita de invenção**: tudo que está marcado [VERIFICAR], mais "
        "qualquer referência cujos dados pareçam inconsistentes (autor que não "
        "trabalha na área, veículo que não existe, ano incompatível).\n"
        "- **Sustentação**: a afirmação central da proposta está apoiada em "
        "alguma referência, ou está solta?\n\n"
        "Formato: '## Auditoria — Proposta N', depois os quatro itens. "
        "Termine cada proposta com uma linha "
        "'**Veredito bibliográfico:** sólido | frágil | não confiável'. "
        "Seja específico: aponte a referência pelo nome, não em geral."
    ),
    output_key="auditoria_bib",
)


# --- 5. Os três crivos, em paralelo -----------------------------------------


def criar_crivo(i: int) -> Agent:
    """O crivo da proposta `i`: viabilidade, originalidade, mérito."""
    return Agent(
        name=f"crivo_{i}",
        model=modelo(),
        description=f"Avalia viabilidade, originalidade e mérito da proposta {i}.",
        instruction=(
            "Estes são os três projetos:\n\n{propostas}\n\n"
            "E esta é a auditoria bibliográfica deles:\n\n{auditoria_bib}\n\n"
            f"Avalie APENAS a Proposta {i}. Ignore as outras duas.\n\n"
            "Dê três notas, cada uma com DUAS frases de justificativa:\n\n"
            "**Viabilidade** (alta | média | baixa) — dá para fazer isso num "
            "mestrado, com dados que existem e método que o grupo domina? O que "
            "é o maior risco de execução?\n\n"
            "**Originalidade** (alta | média | baixa) — isto acrescenta algo ao "
            "que a bibliografia já mostrou, ou repete trabalho feito? Use a "
            "auditoria: proposta apoiada em referência duvidosa não pode "
            "receber originalidade alta.\n\n"
            "**Mérito científico** (alto | médio | baixo) — se der certo, quem "
            "usa o resultado e para quê?\n\n"
            "Termine com uma linha só, exatamente neste formato:\n"
            f"**Proposta {i} — VEREDITO:** aprovada | aprovada com ressalva | reprovada\n\n"
            "Reprove sem constrangimento se for o caso. Três propostas "
            "aprovadas por gentileza não ajudam ninguém."
        ),
        output_key=f"crivo_{i}",
    )


crivos = [criar_crivo(i) for i in range(1, QUANTAS + 1)]

crivo_pronto = JoinNode(name="crivo_pronto")


# --- 6. O plano de desenvolvimento ------------------------------------------

plano = Agent(
    name="plano",
    model=modelo(),
    description="Escreve plano de desenvolvimento para as propostas aprovadas.",
    instruction=(
        "Estes são os três projetos:\n\n{propostas}\n\n"
        "E estes são os pareceres do crivo:\n\n"
        "{crivo_1}\n\n{crivo_2}\n\n{crivo_3}\n\n"
        "Escreva um plano de desenvolvimento para CADA proposta cujo veredito "
        "foi 'aprovada' ou 'aprovada com ressalva'. "
        "Para as reprovadas, escreva uma linha só dizendo que foi reprovada e "
        "qual foi o motivo — não faça plano para elas.\n\n"
        "Cada plano leva:\n"
        "## Plano — Proposta N\n"
        "**Etapas** — de 4 a 6 etapas em ordem, uma linha cada, com duração em "
        "semanas. Some as durações e mostre o total.\n"
        "**Entregas** — o que existe de concreto ao fim de cada etapa.\n"
        "**Primeira semana** — o que a pessoa faz na segunda-feira de manhã.\n"
        "**Risco principal e plano B** — duas frases.\n\n"
        "Se o crivo deu 'aprovada com ressalva', a ressalva tem que aparecer "
        "resolvida em alguma etapa do plano. "
        "Se a auditoria marcou referência duvidosa, a primeira etapa é "
        "verificar essas referências."
    ),
    output_key="planos",
)


# --- 7. O relator ------------------------------------------------------------

relator = Agent(
    name="relator",
    model=modelo(),
    description="Junta tudo num relatório único.",
    instruction=(
        "Monte o relatório final da rodada de propostas. Você tem tudo:\n\n"
        "ESBOÇOS:\n{esbocos}\n\n"
        "PROJETOS:\n{propostas}\n\n"
        "AUDITORIA BIBLIOGRÁFICA:\n{auditoria_bib}\n\n"
        "CRIVO:\n{crivo_1}\n\n{crivo_2}\n\n{crivo_3}\n\n"
        "PLANOS:\n{planos}\n\n"
        "Escreva UM documento em Markdown, nesta estrutura:\n\n"
        "# Relatório de propostas de pesquisa\n\n"
        "## Sumário\n"
        "Uma tabela com uma linha por proposta e as colunas: Nº, Título, "
        "Viabilidade, Originalidade, Mérito, Veredito.\n\n"
        "## Recomendação\n"
        "Dois parágrafos: qual proposta seguir primeiro e por quê; o que "
        "precisa ser resolvido antes de começar.\n\n"
        "## Propostas aprovadas\n"
        "Para cada uma: o projeto (problema, pergunta, método, resultado "
        "esperado), o parecer do crivo resumido, o plano de desenvolvimento e "
        "as referências.\n\n"
        "## Propostas reprovadas\n"
        "Uma seção curta por proposta reprovada, com o motivo.\n\n"
        "## Ressalvas bibliográficas\n"
        "Lista de toda referência marcada como duvidosa ou [VERIFICAR], com a "
        "proposta em que ela aparece. Se não houver nenhuma, diga isso "
        "explicitamente.\n\n"
        "Não invente nada que não esteja acima e não deixe de fora nenhuma "
        "ressalva. Este relatório é a única coisa que a pessoa vai ler."
    ),
    output_key="relatorio",
)


# --- O grafo -----------------------------------------------------------------
#
# Duas correntes. A tupla interna abre o leque (fan-out); o JoinNode seguinte
# fecha (fan-in). Dividir em dois itens é só legibilidade: o grafo é um só, e
# `bibliografia` aparece nas duas porque é onde a primeira corrente termina e a
# segunda começa.
root_agent = Workflow(
    name="pesquisa",
    description=(
        "Pipeline de propostas de pesquisa: esboço, bibliografia em paralelo, "
        "redação, auditoria, crivo em paralelo, plano e relatório."
    ),
    edges=[
        (START, esboco, tuple(pesquisadores), fontes_prontas, redator, bibliografia),
        (bibliografia, tuple(crivos), crivo_pronto, plano, relator),
    ],
)
