"""04_frase — uma frase, três leitores ao mesmo tempo.

Você cola uma frase. Três agentes a reescrevem no mesmo instante — uma versão
simples, uma formal, uma curta — e um relator compara o que saiu. Quatro
chamadas ao modelo. Zero arquivo de dados, zero API: o material é a frase.

    SequentialAgent "frase"
    ├── ParallelAgent "versoes"
    │   ├── simples  → state["versao_simples"]
    │   ├── formal   → state["versao_formal"]
    │   └── curta    → state["versao_curta"]
    └── relator

Os três partem juntos. Cada um vê a instrução dele e a frase que você colou;
quando a frase é ambígua, cada um resolve a ambiguidade do seu jeito. O
relator existe para apontar essa divergência. Use `frases.md` se quiser
frases prontas para colar.

`ParallelAgent` / `SequentialAgent` imprimem aviso de depreciação na 2.x em
favor de `Workflow`; nesta pasta o desenho clássico ainda é o mais legível.

    just web            # escolha 04_frase
    just cli 04_frase"""

from google.adk.agents import Agent, ParallelAgent, SequentialAgent

from modelo import modelo

REGRA_COMUM = (
    "Reescreva a frase que a pessoa acabou de mandar, e só ela. "
    "Devolva a sua versão e mais nada: sem introdução, sem explicação, sem "
    "aspas em volta, sem dizer qual é o seu papel. "
    "Não invente informação que não esteja na frase original. "
    "Se a frase for ambígua, escolha UM sentido e escreva a frase inteira "
    "nesse sentido. "
    "Dois colegas estão reescrevendo a MESMA frase neste instante, para "
    "outros leitores. Você não sabe o que eles escolheram, então não cite, "
    "não comente e não tente combinar com eles."
)

simples = Agent(
    name="simples",
    model=modelo(),
    description="Reescreve em português claro, para qualquer pessoa.",
    instruction=(
        "Você escreve em linguagem simples. Troque termo técnico, jargão e "
        "palavra difícil por palavra do dia a dia. Quebre frase comprida em "
        "duas ou três curtas. Use voz ativa e diga quem faz o quê. "
        "O alvo é alguém de 12 anos entender de primeira. " + REGRA_COMUM
    ),
    output_key="versao_simples",
)

formal = Agent(
    name="formal",
    model=modelo(),
    description="Reescreve no registro formal de documento oficial.",
    instruction=(
        "Você escreve no registro formal de documento oficial brasileiro. "
        "Use terceira pessoa, vocabulário preciso e construção impessoal. "
        "Nada de gíria, nada de abreviação, nada de ponto de exclamação. "
        "Continue sendo uma frase legível, não um monstro de subordinadas. "
        + REGRA_COMUM
    ),
    output_key="versao_formal",
)

curta = Agent(
    name="curta",
    model=modelo(),
    description="Reescreve no menor número de palavras possível.",
    instruction=(
        "Você corta. Reescreva a frase com o menor número de palavras que "
        "ainda preserve o sentido principal. Limite duro: 12 palavras. "
        "Jogue fora rodeio, redundância e educação cerimonial; guarde o "
        "verbo e o essencial. " + REGRA_COMUM
    ),
    output_key="versao_curta",
)

zoomer = Agent(
    name="zoomer",
    model=modelo(),
    description="Reescreve como membro da geração Z.",
    instruction=(
        "Você é geração Z. Você não se importa com seus professores millenials."
        "Você gosta de dançar no TikTok e farmar aura."
        "As respostas não precisam ser compreensíveis." + REGRA_COMUM
    ),
    output_key="versao_zoomer",
)

versoes = ParallelAgent(
    name="versoes",
    description="As três versões, escritas ao mesmo tempo.",
    sub_agents=[simples, formal, curta, zoomer],
)

relator = Agent(
    name="relator",
    model=modelo(),
    description="Compara as três versões e aponta onde elas divergiram.",
    instruction=(
        "Três colegas reescreveram a MESMA frase ao mesmo tempo, sem ver o "
        "trabalho um do outro:\n"
        "- simples (para qualquer pessoa): {versao_simples?}\n"
        "- formal (documento oficial): {versao_formal?}\n"
        "- curta (no máximo 12 palavras): {versao_curta?}\n\n"
        "- zoomer (no máximo 12 palavras): {versao_zoomer?}\n\n"
        "Escreva em três partes, nesta ordem:\n"
        "1. **As três versões** — repita as três, uma por linha, com o rótulo "
        "na frente. Não mude uma vírgula do que eles escreveram.\n"
        "2. **Onde elas divergem** — a diferença de SENTIDO, não de estilo. "
        "Se a frase original era ambígua e cada um escolheu um sentido, é "
        "aqui que isso aparece: diga qual palavra causou e o que cada um "
        "entendeu. Se as três dizem a mesma coisa, diga que a frase original "
        "não era ambígua.\n"
        "3. **Alguém perdeu alguma coisa?** — se alguma versão deixou cair "
        "um dado que estava na frase original, aponte qual e quem. Se "
        "ninguém perdeu nada, diga isso.\n\n"
        "Não escreva uma quarta versão sua. Não elogie."
    ),
)

root_agent = SequentialAgent(
    name="frase",
    description=(
        "Cole uma frase: três agentes a reescrevem ao mesmo tempo, para três "
        "leitores diferentes, e um relator compara."
    ),
    sub_agents=[versoes, relator],
)
