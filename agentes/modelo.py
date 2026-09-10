"""O modelo que as quatro variantes usam — com repetição automática.

POR QUE ISTO EXISTE, EM VEZ DE `model="gemini-3.1-flash-lite"`
---------------------------------------------------------------
A forma curta funciona e é a que aparece em todo tutorial:

    Agent(model="gemini-3.1-flash-lite", ...)

Ela também não repete a chamada quando o servidor recusa. E a cota gratuita do
AI Studio recusa com frequência: medido em 2026-09-09, seis chamadas seguidas a
`gemini-3.1-flash-lite` devolveram **3 sucessos e 3 erros 503**
("This model is currently experiencing high demand").

Para a variante `conversa`, 50% de falha é um Ctrl+C e outra tentativa. Para a
variante `debate`, que faz **doze** chamadas em sequência, é fatal: a chance de
as doze passarem é 0,5¹², ou seja, uma em quatro mil. Foi exatamente isso que
aconteceu — o debate falhou três vezes seguidas antes deste arquivo existir.

A conta é a lição, e ela não é sobre o Gemini: **num sistema de N passos em
série, a confiabilidade de cada passo entra elevada a N.** Encadear agentes
multiplica a fragilidade tão rápido quanto multiplica o custo.

`HttpRetryOptions` resolve a parte mecânica: repete em 429/500/502/503/504,
com espera que dobra a cada tentativa (1 s, 2 s, 4 s...) e um pouco de
aleatoriedade para trinta máquinas da turma não repetirem todas no mesmo
instante.

O que ela NÃO resolve: se o serviço estiver fora do ar de verdade, seis
tentativas só deixam o aluno esperando mais. Repetição compra resiliência
contra falha transitória, não contra indisponibilidade.
"""

from google.adk.models import Gemini
from google.genai import types

NOME = "gemini-3.1-flash-lite"


def modelo() -> Gemini:
    """Devolve o modelo configurado para repetir falhas transitórias.

    É uma função, e não uma constante, porque cada agente recebe a sua própria
    instância — quatro agentes compartilhando um objeto de modelo é o tipo de
    acoplamento que só dá problema depois.
    """
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
