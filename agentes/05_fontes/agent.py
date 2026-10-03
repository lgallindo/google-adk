"""05_fontes — abrir em leque, esperar todo mundo, costurar.

Um tema entra; um esboço propõe ramos; vários pesquisadores buscam fontes em
paralelo; uma barreira (`JoinNode`) espera o último; um relator organiza o
que chegou. O número de ramos é a constante `QUANTAS` (padrão 3): mude um
inteiro e o grafo, o esboço e o relator acompanham.

    START → esboco ─┬→ fontes_1 ─┐
                    ├→ fontes_2 ─┼→ fontes_prontas → relator
                    └→ fontes_3 ─┘

Fan-out é uma tupla na corrente: o ADK dispara os ramos juntos. Fan-in é o
`JoinNode`: ele declara que precisa de todos os predecessores. Um nó comum
com várias entradas roda uma vez por predecessor — o texto sai incompleto num
terminal limpo. A barreira garante o quando; o estado da sessão carrega o
quê (`{esbocos}`, `{fontes_1}`, …).

Os prompts desta pasta vivem aqui por completo. Cada variante do repositório
é um módulo de primeiro nível para o `adk`.

    just web            # escolha 05_fontes
    just cli 05_fontes
"""

# ---------------------------------------------------------------------------
# O QUE VEM DE ONDE
# ---------------------------------------------------------------------------
# `Agent` é o nó que CHAMA o modelo de linguagem. Você descreve em português o
# que ele deve fazer, e a resposta dele vem em português. Os agentes desta
# pasta — o esboço, os pesquisadores e o relator — são todos instâncias desta
# mesma classe: o que muda entre eles é só o texto.
from google.adk.agents import Agent

# Do subpacote `workflow` vêm as três peças do GRAFO:
#
#   START     o nó de entrada. Ele não executa nada: só marca por onde o
#             grafo começa.
#   JoinNode  a barreira que espera TODOS os seus predecessores. É o assunto
#             desta pasta, explicado lá em cima.
#   Workflow  o grafo em si, montado a partir de uma lista de arestas.
from google.adk.workflow import START, JoinNode, Workflow

# `modelo.py` fica na pasta de cima (`agentes/`) e é compartilhado por todas
# as variantes. Ele exporta a função `modelo()`, que devolve o modelo já
# configurado — Gemini na nuvem por padrão; local se `ADK_BACKEND=local`.
# Repare que o import traz a FUNÇÃO, não o modelo: é por
# isso que mais abaixo aparece `modelo()`, com parênteses, dentro de cada
# agente. Cada chamada devolve uma instância nova.
from modelo import modelo

# Constante. MAIÚSCULAS é a convenção do Python para dizer "isto é um valor
# fixo, não mexa enquanto o programa roda" — o Python não impede a mudança,
# quem obedece é quem lê.
#
# E este é o ÚNICO número do arquivo. Troque o 3 por 5, rode de novo, e o
# leque abre em cinco: cinco propostas pedidas, cinco pesquisadores em
# paralelo, cinco bibliografias no relatório. Nada mais precisa mudar.
QUANTAS = 3

# ---------------------------------------------------------------------------
# FRAGMENTOS GERADOS — todo texto que depende de QUANTAS é montado aqui
# ---------------------------------------------------------------------------
# Num lugar só, e de propósito: os agentes lá embaixo continuam sendo texto
# corrido, sem laço nenhum no meio. Se você está lendo este arquivo pela
# primeira vez, pule para o `esboco` e volte depois — daqui saem só três
# pedaços de texto prontos.

# Os números das propostas: 1, 2, 3. Um `range` pode ser percorrido quantas
# vezes você quiser, e é por isso que o mesmo NUMEROS serve aos dois laços
# abaixo. (Um gerador não serviria: ele se esgota na primeira passada.)
NUMEROS = range(1, QUANTAS + 1)

# O formato que o esboço tem que seguir, um cabeçalho por proposta:
#
#     ## Proposta 1
#     <parágrafo>
#     ## Proposta 2
#     <parágrafo>
#     ...
#
# `"".join(...)` cola numa string só os pedaços que o laço vai produzindo, e a
# string vazia da frente é o separador: nada entre um pedaço e o outro.
FORMATO_ESBOCO = "".join(f"## Proposta {i}\n<parágrafo>\n" for i in NUMEROS)

# Os blocos que o relator lê, um por pesquisador:
#
#     BIBLIOGRAFIA DA PROPOSTA 1:
#     {fontes_1}
#
# E aqui está o detalhe mais fino do arquivo. Dentro de uma f-string, `{{` e
# `}}` são como se escreve uma chave LITERAL: o Python as reduz a `{` e `}` e
# não tenta preencher nada. Então `{{fontes_{i}}}` usa as duas coisas na mesma
# expressão — as chaves de fora sobrevivem para o ADK preencher depois, e o
# `{i}` de dentro vira 1, 2 ou 3 agora. Sai o texto `{fontes_1}`, que é
# exatamente o que antes estava escrito à mão.
BLOCOS_DE_FONTES = "".join(
    f"BIBLIOGRAFIA DA PROPOSTA {i}:\n{{fontes_{i}}}\n\n" for i in NUMEROS
)

# O aviso de que os colegas estão rodando ao mesmo tempo. Com `QUANTAS = 1`
# não existem colegas e a frase viraria mentira, então ela é condicional. É um
# `if` comum, escrito no corpo do módulo: roda uma vez só, quando o Python
# carrega o arquivo.
if QUANTAS > 1:
    AVISO_DE_ISOLAMENTO = (
        "Ignore as demais: elas têm outros pesquisadores, e você não sabe o "
        "que eles vão escrever — quando você começou, eles também estavam "
        "começando.\n\n"
    )
else:
    AVISO_DE_ISOLAMENTO = ""

# ---------------------------------------------------------------------------
# NÓ 1 — O ESBOÇO: um agente, argumento por argumento
# ---------------------------------------------------------------------------
# Tudo aqui dentro é passado por ARGUMENTO NOMEADO (`nome=valor`). A ordem não
# importa, e o nome de cada um diz o que ele é — por isso a chamada ocupa
# quinze linhas em vez de uma.
esboco = Agent(
    # A identidade do nó dentro do grafo. Dois nós não podem repetir o mesmo
    # nome, e é este nome que você vê na interface do `adk web`.
    name="esboco",
    # O modelo que este agente usa. Parênteses: estamos CHAMANDO a função.
    model=modelo(),
    # Uma linha sobre o papel do agente, para humano ler. Não faz parte do
    # prompt: o modelo não recebe este texto.
    description=f"Gera {QUANTAS} propostas de pesquisa a partir de um tema.",
    # A INSTRUÇÃO é o prompt de sistema: o texto que o modelo lê antes da
    # pergunta da pessoa. Duas coisas de Python para reparar aqui:
    #
    # 1. STRINGS COLADAS. Literais um embaixo do outro, dentro de parênteses,
    #    viram UMA string só — sem `+`, sem vírgula. A quebra em várias linhas
    #    é só para o código caber na tela; o modelo recebe tudo emendado. Uma
    #    vírgula esquecida entre duas delas transforma isto numa tupla, e o
    #    erro só aparece bem longe daqui.
    #
    # 2. ALGUMAS LINHAS TÊM `f` E OUTRAS NÃO, e isso é de propósito.
    #    `f"...{QUANTAS}..."` é interpolação do PYTHON: vira o texto "3" agora,
    #    no instante em que o agente é criado. As chaves das linhas SEM `f`
    #    (veja `{esbocos}`, logo abaixo no pesquisador) ficam intactas, porque
    #    quem as substitui é o ADK, depois, com o estado da sessão. Pôr `f` na
    #    linha errada apaga esse buraco; esquecer o `f` na linha certa manda a
    #    palavra "QUANTAS" entre chaves para o modelo.
    instruction=(
        "A pessoa vai te dar um TEMA de pesquisa. "
        f"Proponha exatamente {QUANTAS} propostas de pesquisa distintas sobre "
        f"esse tema, numeradas de 1 a {QUANTAS}, um PARÁGRAFO cada.\n\n"
        "Cada parágrafo precisa deixar claro a pergunta de pesquisa, o que "
        "seria investigado e por que isso importa. As propostas têm que ser "
        "mesmo diferentes entre si, e não variações da mesma coisa.\n\n"
        # O formato é combinado, e não enfeite: cada pesquisador vai procurar
        # o SEU "## Proposta N" no texto que sair daqui. Prompt que produz
        # entrada para outro prompt precisa ser previsível. O bloco vem
        # pronto de FORMATO_ESBOCO, com uma linha por proposta.
        "Use exatamente este formato, porque os pesquisadores contam com ele:\n"
        f"{FORMATO_ESBOCO}\n"
        "Não escreva nada antes nem depois."
    ),
    # O CORREIO ENTRE OS NÓS. `output_key` grava a resposta deste agente no
    # estado da sessão, na chave "esbocos". Quem quiser ler escreve
    # `{esbocos}` na própria instrução — é exatamente o que todos os
    # pesquisadores fazem logo abaixo. O grafo manda no QUANDO; o estado
    # carrega o QUÊ.
    output_key="esbocos",
)


# ---------------------------------------------------------------------------
# OS PESQUISADORES, SAÍDOS DE UMA FÁBRICA — um por proposta
# ---------------------------------------------------------------------------
# `i: int` e `-> Agent` são ANOTAÇÕES DE TIPO: dizem que o parâmetro é um
# número inteiro e que a função devolve um `Agent`. O Python não confere isso
# sozinho ao rodar; elas existem para quem lê o código e para o editor avisar
# quando algo não bate.
def criar_pesquisador(i: int) -> Agent:
    """O pesquisador da proposta `i`.

    Uma fábrica, e não vários blocos copiados, porque a única diferença entre
    eles é o NÚMERO da proposta. Cada chamada devolve um agente novo, com nome
    e `output_key` próprios: dois nós do grafo não podem ter o mesmo nome, e
    duas chaves de estado iguais se sobrescreveriam.

    É também o que permite trocar `QUANTAS`: a fábrica é chamada quantas vezes
    for preciso, e nenhum agente precisa ser escrito à mão.
    """
    return Agent(
        # f-string de novo, e agora ela é essencial: é ela que faz os nomes
        # saírem diferentes — "fontes_1", "fontes_2", "fontes_3", ...
        name=f"fontes_{i}",
        model=modelo(),
        description=f"Levanta bibliografia comentada da proposta {i}.",
        instruction=(
            # SEM `f`: estas chaves têm que chegar inteiras no ADK, que as
            # troca pelo que o esboço escreveu no estado.
            "Estas são as propostas que foram esboçadas:\n\n"
            "{esbocos}\n\n"
            # COM `f`: o número da proposta precisa virar um valor aqui e
            # agora, senão todos os pesquisadores fariam a mesma coisa.
            f"Trabalhe APENAS na Proposta {i}.\n\n"
            # Este parágrafo não é estilo, é aritmética: todos começam no
            # mesmo instante, então quando este monta o prompt dele os outros
            # ainda não escreveram nada. Não há o que ler. Estado escrito
            # ANTES da largada todo mundo enxerga; estado escrito DENTRO do
            # bloco paralelo, ninguém. (Com QUANTAS = 1 o aviso some: veja
            # AVISO_DE_ISOLAMENTO lá em cima.)
            f"{AVISO_DE_ISOLAMENTO}"
            "Entregue duas coisas:\n\n"
            "**Bibliografia comentada** — de 5 a 6 trabalhos relevantes. Para "
            "cada um: referência (autores, título, veículo, ano) e DUAS frases "
            "dizendo o que o trabalho mostra e por que importa para esta "
            "proposta.\n\n"
            "**Fichamentos** — os 2 trabalhos mais centrais, um fichamento "
            "cada: problema atacado, método, resultado principal e a lacuna "
            "que ele deixa aberta.\n\n"
            # O modelo não tem acesso a biblioteca nenhuma: ele escreve de
            # memória, e memória de modelo inventa referência com cara de
            # verdadeira. Pedir a marca [VERIFICAR] não resolve o problema,
            # mas deixa o rastro visível para quem for conferir depois.
            "⚠ Você está trabalhando de memória, sem buscar em base nenhuma. "
            "Marque com [VERIFICAR] toda referência de que você não tenha "
            "certeza. Quatro referências marcadas valem mais que seis "
            "inventadas com cara de certas."
        ),
        # Uma chave de estado por pesquisador: "fontes_1", "fontes_2", ...
        # Se fossem todas iguais, a última a terminar apagaria as outras — e
        # sem erro nenhum na tela.
        output_key=f"fontes_{i}",
    )


# Uma LIST COMPREHENSION. Lê-se: "para cada i em NUMEROS, crie um pesquisador
# e guarde na lista". É a forma curta de um `for` com `lista.append(...)`.
#
# `NUMEROS` é o `range(1, QUANTAS + 1)` definido lá em cima: 1, 2, 3 — o
# primeiro número entra, o último fica de fora, daí o `+ 1`. Começa em 1, e
# não no 0 de costume, porque este número tem que bater com o "Proposta 1" que
# o esboço escreveu.
pesquisadores = [criar_pesquisador(i) for i in NUMEROS]

# A barreira. Repare no que ela NÃO tem: nem `model`, nem `instruction`, nem
# `output_key`. Ela não chama modelo e não escreve texto — o trabalho dela é
# inteiramente sobre TEMPO: segurar o grafo até o último pesquisador terminar.
# Um só `JoinNode` dá conta de qualquer número de ramos: ele descobre quantos
# predecessores tem olhando as arestas do grafo.
fontes_prontas = JoinNode(name="fontes_prontas")

# ---------------------------------------------------------------------------
# O RELATOR: quem de fato escreve o documento
# ---------------------------------------------------------------------------
relator = Agent(
    name="relator",
    model=modelo(),
    description="Relata num documento único o esboço e a bibliografia de cada proposta.",
    # Nenhuma chave desta instrução é preenchida pelo Python: TODAS são
    # buracos que o ADK preenche com o estado da sessão, na hora de rodar. As
    # de `{esbocos}` estão numa linha sem `f`; as de `{fontes_1}`, `{fontes_2}`
    # e companhia vêm prontas em BLOCOS_DE_FONTES, onde `{{` e `}}` já as
    # protegeram. Interpolar um valor com `f"{BLOCOS_DE_FONTES}"` NÃO reprocessa
    # o texto inserido: a f-string olha a linha que você escreveu, não o miolo
    # do que veio de fora.
    #
    # E repare de onde vem cada uma: do estado, escrito por `output_key`, e não
    # do dicionário que a barreira repassou. A barreira garantiu o QUANDO;
    # estas chaves são o QUÊ.
    instruction=(
        "Monte o relatório desta rodada de levantamento. Você tem tudo:\n\n"
        "ESBOÇOS DAS PROPOSTAS:\n{esbocos}\n\n"
        f"{BLOCOS_DE_FONTES}"
        "Escreva UM documento em Markdown, nesta estrutura:\n\n"
        "# Levantamento de propostas de pesquisa\n\n"
        "## Sumário\n"
        "Uma tabela com uma linha por proposta e as colunas: Nº, Assunto em "
        "poucas palavras, Quantas referências, Quantas marcadas [VERIFICAR].\n\n"
        "## Proposta N — <assunto>\n"
        "Para cada proposta, nesta ordem: o esboço como ele foi escrito, a "
        "bibliografia comentada e os fichamentos.\n\n"
        "## Referências a verificar\n"
        "Lista de toda referência marcada com [VERIFICAR], dizendo em qual "
        "proposta ela aparece. Se não houver nenhuma, diga isso "
        "explicitamente.\n\n"
        "## O que este levantamento ainda não responde\n"
        "Três a cinco linhas: o que falta saber antes de escolher uma das "
        "propostas para desenvolver.\n\n"
        # As três proibições abaixo existem porque um modelo, deixado solto,
        # faz exatamente essas três coisas: desenvolve o que era esboço, limpa
        # as marcas de incerteza e elege um vencedor que ninguém pediu.
        "Você RELATA, não desenvolve: não transforme esboço em projeto, não "
        "acrescente método que ninguém escreveu e não invente referência que "
        "não esteja acima. "
        "Preserve as marcas [VERIFICAR] — não limpe o que o pesquisador marcou "
        "como incerto. "
        "Também não escolha a melhor proposta: esta rodada é de levantamento, e "
        "a escolha é de quem lê."
    ),
    # Último nó do grafo: ninguém lê esta chave. Ela fica no estado mesmo
    # assim, disponível para quem for inspecionar a sessão depois.
    output_key="relatorio",
)

# ---------------------------------------------------------------------------
# O GRAFO — e ele é uma linha só
# ---------------------------------------------------------------------------
# `edges` é uma LISTA de correntes; aqui há uma corrente só, escrita como
# TUPLA. Numa corrente, cada item aponta para o seguinte:
#
#     START → esboco → (os pesquisadores, ao mesmo tempo) → fontes_prontas
#             → relator
#
# `tuple(pesquisadores)` converte a lista em tupla, e a troca não é enfeite:
# dentro da corrente, é a TUPLA que significa "dispare todos estes em
# paralelo". O ADK testa literalmente `isinstance(alvo, tuple)`; uma lista
# nesse lugar não é fan-out. A fábrica devolve lista porque list comprehension
# devolve lista — a conversão acontece aqui, no ponto em que o tipo passa a
# ter significado.
#
# Esta linha não menciona QUANTAS, e é justamente por isso que ela não muda:
# a tupla tem o tamanho que a lista tiver. Se você subir muito o número, é
# aqui que entra `max_concurrency=4` — o leque continua inteiro, mas o ADK
# segura quantos correm de cada vez.
#
# `root_agent` é o nome que o `adk` procura ao carregar a pasta. Com outro
# nome, a variante simplesmente não aparece no `adk web`.
root_agent = Workflow(
    name="fontes",
    description=(
        f"Esboça {QUANTAS} propostas, levanta a bibliografia de todas em "
        "paralelo e relata tudo num documento."
    ),
    edges=[(START, esboco, tuple(pesquisadores), fontes_prontas, relator)],
)
