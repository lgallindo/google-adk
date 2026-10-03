"""06_debate — três vozes, duas rodadas, um julgamento.

O `root_agent` é um orquestrador: um `SequentialAgent` cuja primeira peça é
um `LoopAgent` com três debatedores, e a segunda é o mediador.

    SequentialAgent "debate"
    ├── LoopAgent "rodadas"  (max_iterations=2)
    │   ├── otimista   → state["arg_otimista"]
    │   ├── cetico     → state["arg_cetico"]
    │   └── pragmatico → state["arg_pragmatico"]
    └── mediador

Sete chamadas ao modelo por pergunta (3 × 2 + 1). Custo e latência
multiplicam; a tela segue igual à de um agente só.

Eles conversam por `output_key`: cada um grava a fala numa chave; os outros
leem `{arg_otimista}` na instrução. Na rodada 2 a chave é regravada — a fala
da rodada 1 sai do estado. O mediador recebe a última rodada pelas chaves; o
histórico da conversa ainda carrega o resto. O tema é o que a pessoa digitar.

    just web            # escolha 06_debate
    just cli 06_debate"""

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
