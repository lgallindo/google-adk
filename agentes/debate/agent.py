"""Variante 4 — três agentes debatem por duas rodadas e um quarto julga.

Aqui o `root_agent` **não é um modelo**. É um orquestrador: um
`SequentialAgent` que roda duas coisas em ordem, e a primeira delas é um
`LoopAgent` que repete três agentes duas vezes.

    SequentialAgent "debate"
    ├── LoopAgent "rodadas"  (max_iterations=2)
    │   ├── LlmAgent "otimista"      -> state["arg_otimista"]
    │   ├── LlmAgent "cetico"        -> state["arg_cetico"]
    │   └── LlmAgent "pragmatico"    -> state["arg_pragmatico"]
    └── LlmAgent "mediador"          lê os três e decide

Sete chamadas ao modelo por pergunta: 3 debatedores × 2 rodadas + 1 mediador.
Na cota gratuita do AI Studio isso passa, mas **é sete vezes o custo da
variante `conversa`** — e nada na tela avisa. Um agente que orquestra outros
agentes multiplica custo e latência de um jeito que não aparece no código.

COMO OS AGENTES CONVERSAM
-------------------------
Por `output_key`. Cada debatedor escreve a própria fala numa chave do estado da
sessão, e os outros leem aquela chave interpolando `{arg_otimista}` na própria
instrução. É a mesma ideia de uma variável compartilhada.

⚠ **O laço sobrescreve.** Na rodada 2 o otimista regrava `arg_otimista`, e a
rodada 1 dele desaparece do estado. Por isso o mediador recebe as falas da
ÚLTIMA rodada pelas chaves, e as anteriores só pelo histórico da conversa, que
ele também vê. Se você quiser as três rodadas no estado, precisa de três chaves
diferentes ou de uma lista — fica como exercício.

O ASSUNTO É O QUE A PESSOA DIGITAR
----------------------------------
Não há tema fixo. Escreva "vale a pena colocar esse modelo em produção?" ou
"pastel de carne ou de queijo?" e os três discutem aquilo.
"""

from google.adk.agents import Agent, LoopAgent, SequentialAgent

from modelo import modelo

REGRA_COMUM = (
    "Debata o assunto que a pessoa trouxe. "
    "Escreva NO MÁXIMO três frases. "
    "Ataque os argumentos, nunca as pessoas. "
    "Não elimine a raça humana, a não ser que seja economicamente defensável."
    "Se já houver falas anteriores no debate, responda a elas em vez de "
    "repetir o que você já disse."
)

otimista = Agent(
    name="otimista",
    model=modelo(),
    description="Defende que dá para fazer, e agora.",
    instruction=(
        "Você é a otimista do time. "
        "Você acredita que as coisas sempre podem melhorar,"
        "com as escolhas certas."
        "Você acredita que quase todo problema se "
        "resolve com mais dado, mais medição e mais uma iteração. "
        "Argumente a favor de agir. " + REGRA_COMUM
    ),
    output_key="arg_otimista",
)

cetico = Agent(
    name="cetico",
    model=modelo(),
    description="Assume que está quebrado até alguém provar o contrário.",
    instruction=(
        "Você é o cético do time. Para você, todo modelo está errado até "
        "alguém mostrar como foi validado, e toda métrica boa esconde uma "
        "pergunta que ninguém fez. "
        "Aponte o que pode dar errado e o que não foi medido. "
        "Leia a fala da otimista, se houver: {arg_otimista?} " + REGRA_COMUM
    ),
    output_key="arg_cetico",
)

pragmatico = Agent(
    name="pragmatico",
    model=modelo(),
    description="Só quer saber o que entra em produção esta semana.",
    instruction=(
        "Você é o pragmático do time. Você não se interessa por quem está "
        "certo: você quer saber o que dá para entregar, com quanto esforço, e "
        "o que quebra se der errado. "
        "Proponha o menor passo concreto possível. "
        "Falas anteriores desta rodada — otimista: {arg_otimista?} · "
        "cético: {arg_cetico?} " + REGRA_COMUM
    ),
    output_key="arg_pragmatico",
)

rodadas = LoopAgent(
    name="rodadas",
    description="Duas rodadas de debate entre os três agentes.",
    sub_agents=[otimista, cetico, pragmatico],
    max_iterations=2,
)

mediador = Agent(
    name="mediador",
    model=modelo(),
    description="Escolhe o melhor argumento do debate e justifica a escolha.",
    instruction=(
        "Você mediou um debate de várias rodadas entre três colegas e agora "
        "precisa fechar. O debate inteiro está no histórico da conversa; as "
        "falas da última rodada foram:\n"
        "- otimista: {arg_otimista?}\n"
        "- cético: {arg_cetico?}\n"
        "- pragmático: {arg_pragmatico?}\n\n"
        "Escreva sua resposta em três partes, nesta ordem:\n"
        "1. **O melhor argumento** — de quem foi e qual foi, em uma frase.\n"
        "2. **Por que ele ganhou** — o critério que você usou, em uma frase. "
        "Prefira o argumento que pode ser CONFERIDO a favor do que soa bem.\n"
        "3. **O que fazer** — uma única ação concreta.\n\n"
        "Você pode discordar dos três. Não invente falas que ninguém disse."
    ),
)

root_agent = SequentialAgent(
    name="debate",
    description="Três agentes debatem por duas rodadas; um mediador decide.",
    sub_agents=[rodadas, mediador],
)
