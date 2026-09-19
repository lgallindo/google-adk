"""Variante 4d — uma frase, três versões ao mesmo tempo.

É a [`paralelo`](../paralelo/) sem nada em volta: sem ferramenta, sem arquivo
de dados, sem gabarito, sem busca. Você cola UMA frase e três agentes a
reescrevem ao mesmo tempo, cada um para um leitor diferente.

    SequentialAgent "frase"
    ├── ParallelAgent "versoes"      ← as três ao mesmo tempo
    │   ├── LlmAgent "simples"  -> state["versao_simples"]
    │   ├── LlmAgent "formal"   -> state["versao_formal"]
    │   └── LlmAgent "curta"    -> state["versao_curta"]
    └── LlmAgent "relator"           compara as três

Quatro chamadas ao modelo por frase.

POR QUE ESTA VARIANTE EXISTE
----------------------------
Para mostrar `ParallelAgent` sem que a turma precise entender mais nada. Não
há pedido de LAI para ler, nem protocolo para decorar, nem tabela para
consultar: o que entra é a frase que você colar, e o que sai são três versões
dela. Dá para fazer com qualquer frase que apareça na tela — do edital, do
e-mail que você acabou de receber, do slide anterior.

Use `frases.md` se quiser frases já prontas para colar.

A IDEIA, DE NOVO
----------------
Os três **não se escutam**. Eles começam no mesmo instante, então nenhum
consegue ler o que o outro escreveu. Cada um vê só a sua instrução e a frase
que você colou.

E é exatamente por isso que o exercício funciona: quando a frase é ambígua,
os três resolvem a ambiguidade de jeitos DIFERENTES, porque nenhum soube o
que o outro decidiu. O relator existe para apontar essa divergência. Numa
fila (`SequentialAgent`) isso não aconteceria: o segundo leria a escolha do
primeiro e iria atrás.

⚠ DEPRECIADO NA 2.8.0
---------------------
`ParallelAgent`, `SequentialAgent` e `LoopAgent` imprimem um aviso de
depreciação na 2.x, em favor do `Workflow` — veja [`fluxo`](../fluxo/). Nada
quebra; é o jeito clássico, não o novo.
"""

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
