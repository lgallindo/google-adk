"""Variante 4b — o mesmo debate da variante 4, com o estado consertado.

A variante `debate` funciona e tem três defeitos de **estado**, todos anotados
no cabeçalho dela. Esta pasta é a resposta a eles. Nada aqui muda o formato do
debate: continuam três debatedores, **duas** rodadas, um mediador e sete chamadas
ao modelo. O que muda é **o que sobra no estado da sessão quando acaba**.

OS TRÊS DEFEITOS, E O QUE CADA UM VIROU AQUI
--------------------------------------------
1. `output_key` **sobrescreve**. Na rodada 2 o otimista regrava
   `arg_otimista` e a fala da rodada 1 desaparece do estado. `output_key` sabe
   atribuir, não sabe acrescentar.
   → Cada debatedor ganhou um `after_agent_callback` (`registrar`) que copia a
     fala recém-escrita para o fim de uma LISTA em `state["ata"]`. A lista
     cresce: seis falas ao final, com rodada e autor em cada uma.

2. O mediador da variante 4 lê só a ÚLTIMA rodada pelas chaves; a
   primeira chega a ele apenas pelo histórico da conversa — que é uma coisa
   que ele vê, mas que você não controla nem consegue inspecionar.
   → Aqui o mediador lê a ata inteira, montada em Python, na ordem, com rótulo
     de rodada. O que ele recebe você consegue ler na aba **State** do
     `adk web`.

3. Leitura **assimétrica**: quem fala primeiro na rodada não lê nada pelas
   chaves (o otimista da variante 4 não tem nenhum `{...}` na instrução), o
   segundo lê uma e o terceiro lê duas. Os três estavam olhando para estados
   diferentes, e isso não estava escrito em lugar nenhum.
   → Todos os três recebem a MESMA transcrição, montada pela mesma função. O
     otimista da rodada 2 agora lê a rodada 1 pelo estado, e não por sorte.

A FERRAMENTA NOVA: INSTRUÇÃO QUE É FUNÇÃO
-----------------------------------------
`instruction=` aceita uma string (com `{chave}` interpolado pelo ADK) **ou uma
função** que recebe o contexto e devolve a string. Uma lista não cabe na forma
string — `{ata}` renderizaria o `repr` do Python na cara do modelo. Então aqui
a instrução é função, e a transcrição é montada com um `for`.

Duas consequências que valem saber:

- Quando a instrução é função, o ADK **não** interpola `{}` no resultado. As
  chaves que sobrarem no texto chegam literais ao modelo. Você ganha o controle
  e perde o açúcar.
- `state` no contexto de leitura é somente-leitura de propósito. Quem escreve é
  o callback, que recebe um contexto de escrita.

O CUSTO DA CORREÇÃO
-------------------
Não são mais chamadas: continuam sete. São mais **tokens** — a ata vai no
prompt de todo mundo e o histórico da conversa continua indo também, então a
mesma informação viaja duas vezes. Dá para cortar a duplicação com
`include_contents="none"`, e aí o estado passa a ser a única fonte; o preço é
que a pergunta da pessoa também sai do prompt e você precisa injetá-la à mão a
partir de `ctx.user_content`. Fica como exercício.

O QUE ESTA VARIANTE NÃO CONSERTA
--------------------------------
O estado ainda morre com o processo, porque quem escolhe onde guardar sessão
não é este arquivo — é quem sobe o servidor. `just web` usa memória.
`just web-memoria` sobe o mesmo servidor com um SQLite ao lado, e aí a ata
sobrevive a um Ctrl+C.
"""

from collections.abc import Mapping
from typing import Any, Callable

from google.adk.agents import Agent, LoopAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.readonly_context import ReadonlyContext

from modelo import modelo

RODADAS = 2

REGRA_COMUM = (
    "Debata o assunto que a pessoa trouxe. "
    "Escreva NO MÁXIMO três frases. "
    "Ataque os argumentos, nunca as pessoas. "
    "Responda ao que já foi dito em vez de repetir o que você mesmo disse."
)

PAPEIS = {
    "otimista": (
        "Você é a otimista do time. Você acredita que quase todo problema se "
        "resolve com mais dado, mais medição e mais uma iteração. "
        "Argumente a favor de agir."
    ),
    "cetico": (
        "Você é o cético do time. Para você, todo modelo está errado até "
        "alguém mostrar como foi validado, e toda métrica boa esconde uma "
        "pergunta que ninguém fez. "
        "Aponte o que pode dar errado e o que não foi medido."
    ),
    "pragmatico": (
        "Você é o pragmático do time. Você não se interessa por quem está "
        "certo: você quer saber o que dá para entregar, com quanto esforço, e "
        "o que quebra se der errado. "
        "Proponha o menor passo concreto possível."
    ),
}


# --------------------------------------------------------------------------
# ESTADO: quem escreve
# --------------------------------------------------------------------------
# Duas chaves, e só duas:
#
#     state["rodada"]  int   em que rodada o debate está (1, 2, 3)
#     state["ata"]     list  uma entrada por fala: {rodada, quem, fala}
#
# As chaves `arg_*` do `output_key` continuam existindo, porque é assim que a
# fala sai do modelo e entra no estado — mas ninguém mais lê elas na instrução.
# Elas são a caixa de entrada do callback, não a memória do debate.


def abrir_rodada(callback_context: CallbackContext) -> None:
    """Incrementa o contador de rodada. Roda antes da primeira fala de cada uma.

    O `LoopAgent` guarda um contador de iterações por dentro, mas ele é
    detalhe de implementação e não aparece no estado que você inspeciona. Um
    inteiro nosso, numa chave nossa, aparece — e é o que os debatedores leem
    para saber onde estão.

    O acoplamento aqui é real e vale dizer em voz alta: este callback está no
    otimista **porque ele é o primeiro da lista**. Troque a ordem dos
    `sub_agents` e o contador precisa mudar de agente junto.
    """
    rodada = callback_context.state.get("rodada", 0) + 1
    callback_context.state["rodada"] = rodada
    return None


def registrar(callback_context: CallbackContext) -> None:
    """Copia a fala que o `output_key` acabou de gravar para o fim da ata.

    Roda depois do agente, quando `state["arg_<nome>"]` já tem a fala desta
    rodada — e antes de a próxima rodada sobrescrever aquela chave. É essa
    janela que a variante 4 não usa.

    Repare no `list(...)`: a ata é **recriada e reatribuída**, nunca alterada
    no lugar. `state[chave] = valor` é o que registra a mudança para ser
    gravada; um `.append()` no objeto que estava lá dentro muda o valor na
    memória e não avisa ninguém. Com sessão em memória isso passa despercebido
    (é o mesmo objeto), e é exatamente o tipo de bug que só aparece no dia em
    que você liga o banco.
    """
    quem = callback_context.agent_name
    fala = str(callback_context.state.get(f"arg_{quem}") or "").strip()
    if not fala:
        # O modelo pode devolver vazio (recusa, filtro, 503 que sobreviveu às
        # seis tentativas). Ata com fala em branco é pior que ata com um furo:
        # o mediador contaria uma fala que não existe.
        return None

    ata = list(callback_context.state.get("ata", []))
    ata.append(
        {
            "rodada": callback_context.state.get("rodada", 0),
            "quem": quem,
            "fala": fala,
        }
    )
    callback_context.state["ata"] = ata
    return None


# --------------------------------------------------------------------------
# ESTADO: quem lê
# --------------------------------------------------------------------------


def transcrever(estado: Mapping[str, Any]) -> str:
    """Devolve a ata inteira como texto, na ordem, com rótulo de rodada."""
    ata = estado.get("ata") or []
    if not ata:
        return "(ninguém falou ainda — você abre o debate.)"
    return "\n".join(
        f"[rodada {e['rodada']}] {e['quem']}: {e['fala']}" for e in ata
    )


def instrucao_de(nome: str) -> Callable[[ReadonlyContext], str]:
    """Monta a instrução de um debatedor a partir do estado, na hora da chamada.

    Os três debatedores usam esta mesma função, então recebem a mesma
    transcrição pela mesma regra. A única diferença entre eles é o papel — que
    é o que a gente queria que fosse a única diferença.
    """

    def construir(ctx: ReadonlyContext) -> str:
        return (
            f"{PAPEIS[nome]}\n\n"
            f"Você está na rodada {ctx.state.get('rodada', 1)} de {RODADAS}.\n\n"
            f"DEBATE ATÉ AGORA (todas as rodadas, na ordem):\n"
            f"{transcrever(ctx.state)}\n\n"
            f"{REGRA_COMUM}"
        )

    return construir


def instrucao_do_mediador(ctx: ReadonlyContext) -> str:
    """Monta a instrução do mediador com a ata inteira e a contagem de falas.

    A contagem é feita em Python, não pelo modelo. Ela serve para transformar
    "não invente falas" em algo conferível: se o mediador citar uma quarta
    pessoa, a ata na tela desmente ele.
    """
    ata = ctx.state.get("ata") or []
    rodadas_vistas = sorted({e["rodada"] for e in ata})
    return (
        "Você mediou um debate entre três colegas e agora precisa fechar.\n\n"
        f"A ata tem {len(ata)} falas, nas rodadas {rodadas_vistas or '—'}. "
        "Ela está inteira aqui embaixo; não existe nenhuma fala fora dela.\n\n"
        f"ATA DO DEBATE:\n{transcrever(ctx.state)}\n\n"
        "Escreva sua resposta em três partes, nesta ordem:\n"
        "1. **O melhor argumento** — de quem foi, em que rodada, e qual foi, "
        "em uma frase.\n"
        "2. **Por que ele ganhou** — o critério que você usou, em uma frase. "
        "Prefira o argumento que pode ser CONFERIDO a favor do que soa bem.\n"
        "3. **O que mudou entre a primeira e a última rodada** — uma frase. "
        "Se não mudou nada, diga que não mudou: rodadas que não movem "
        "ninguém são sete chamadas ao modelo para nada.\n"
        "4. **O que fazer** — uma única ação concreta.\n\n"
        "Você pode discordar dos três. Cite apenas falas que estão na ata."
    )


# --------------------------------------------------------------------------
# OS AGENTES
# --------------------------------------------------------------------------

otimista = Agent(
    name="otimista",
    model=modelo(),
    description="Defende que dá para fazer, e agora.",
    instruction=instrucao_de("otimista"),
    output_key="arg_otimista",
    before_agent_callback=abrir_rodada,
    after_agent_callback=registrar,
)

cetico = Agent(
    name="cetico",
    model=modelo(),
    description="Assume que está quebrado até alguém provar o contrário.",
    instruction=instrucao_de("cetico"),
    output_key="arg_cetico",
    after_agent_callback=registrar,
)

pragmatico = Agent(
    name="pragmatico",
    model=modelo(),
    description="Só quer saber o que entra em produção esta semana.",
    instruction=instrucao_de("pragmatico"),
    output_key="arg_pragmatico",
    after_agent_callback=registrar,
)

rodadas = LoopAgent(
    name="rodadas",
    description="Três rodadas de debate, registradas em ata.",
    sub_agents=[otimista, cetico, pragmatico],
    max_iterations=RODADAS,
)

mediador = Agent(
    name="mediador",
    model=modelo(),
    description="Lê a ata inteira, escolhe o melhor argumento e justifica.",
    instruction=instrucao_do_mediador,
)

root_agent = SequentialAgent(
    name="ata",
    description="O debate da variante 4, com as duas rodadas guardadas em ata.",
    sub_agents=[rodadas, mediador],
)
