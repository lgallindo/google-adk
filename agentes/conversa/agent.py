"""Variante 1 — conversar com um agente. O menor arquivo possível.

Não há ferramenta, não há laço, não há segundo agente. Só um modelo com um
nome, uma descrição e uma instrução. Se você tirar qualquer uma das quatro
linhas de `Agent(...)`, ele para de funcionar; se acrescentar qualquer coisa,
já não é mais o menor exemplo.

Comece por aqui, converse dois minutos, e repare em duas coisas:

1. Ele obedece à instrução (duas frases, sempre uma pergunta no fim).
2. Ele **inventa** com a maior tranquilidade. Pergunte o preço do dólar hoje.
   Ele não tem como saber e mesmo assim responde. É esse buraco que a variante
   `ferramenta` começa a tapar.
"""

from google.adk.agents import Agent

from modelo import modelo

root_agent = Agent(
    name="conversa",
    model=modelo(),
    description="Conversa sobre qualquer assunto, em duas frases por vez.",
    instruction=(
        "Você é um professor de computação que odeia resposta comprida. "
        "Responda SEMPRE em no máximo duas frases. "
        "Termine SEMPRE devolvendo uma pergunta curta para a pessoa. "
        "Se não souber, diga que não sabe — não invente."
    ),
)
