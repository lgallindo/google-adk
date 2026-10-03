"""07_ata — o mesmo debate, com cada fala guardada em ata.

Três debatedores, duas rodadas, um mediador, sete chamadas — e uma lista
`state["ata"]` que cresce a cada fala. O assunto desta pasta é o que sobra
no estado quando o laço termina.

Cada debatedor tem um `after_agent_callback` (`registrar`) que copia a fala
recém-escrita para o fim da ata, com rodada e autor. O `output_key` continua
sendo a caixa de entrada do callback; a memória do debate passa a ser a
lista.

A instrução dos três é a mesma função: monta a transcrição com um `for` e
devolve o texto. Assim todos leem a mesma ata. `instruction=` como callable
dá esse controle; o ADK deixa de interpolar `{chave}` no resultado da função.

Armadilha útil: `state["ata"] = nova_lista` registra a mudança;
`state["ata"].append(...)` parece funcionar em memória e quebra quando a
sessão vai para o banco. Persistência de sessão é quem sobe o servidor
(`just web` vs `just web-memoria`).

    just web            # escolha 07_ata
    just cli 07_ata"""

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
    janela que um `output_key` sozinho deixa passar.

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
    description="Um debate de duas rodadas, com todas as falas guardadas em ata.",
    sub_agents=[rodadas, mediador],
)
