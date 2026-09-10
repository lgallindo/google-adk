"""O modelo, com repetição automática em falha transitória.

POR QUE ISTO EXISTE, EM VEZ DE `model="gemini-3.1-flash-lite"`
---------------------------------------------------------------
A forma curta é a de todo tutorial, e ela não repete a chamada quando o
servidor recusa. A cota gratuita do AI Studio recusa com frequência: medido em
2026-09-09, seis chamadas seguidas a `gemini-3.1-flash-lite` devolveram **3
sucessos e 3 erros 503** ("This model is currently experiencing high demand").

Com uma chamada por pergunta, 503 é um Ctrl+C e outra tentativa. Ainda assim
não se dá aula com 50% de chance de a demonstração falhar na frente da turma.

`HttpRetryOptions` repete em 429/500/502/503/504, com espera que dobra a cada
tentativa (1 s, 2 s, 4 s...) e um pouco de aleatoriedade, para trinta máquinas
da turma não repetirem todas no mesmo instante.

Repetição compra resiliência contra falha **transitória**. Se o serviço estiver
fora do ar de verdade, seis tentativas só fazem o aluno esperar mais.

> Este arquivo é uma cópia deliberada. Cada pasta de aula se sustenta sozinha,
> então nenhuma delas importa código de outra — o preço é ter a mesma fábrica
> em mais de um lugar, e ele é mais barato que uma aula que não sobe porque a
> pasta vizinha mudou.
"""

from google.adk.models import Gemini
from google.genai import types

NOME = "gemini-3.1-flash-lite"


def modelo() -> Gemini:
    """Devolve o modelo configurado para repetir falhas transitórias."""
    return Gemini(
        model=NOME,
        retry_options=types.HttpRetryOptions(
            attempts=6,
            initial_delay=1.0,
            max_delay=30.0,
            exp_base=2.0,
            jitter=0.3,
            http_status_codes=[429, 500, 502, 503, 504],
        ),
    )
