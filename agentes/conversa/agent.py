"""conversa — conversar com um agente. O menor arquivo possível.

Não há ferramenta, não há laço, não há segundo agente. Só um modelo com um
nome, uma descrição e uma instrução. Se você tirar qualquer uma das quatro
linhas de `Agent(...)`, ele para de funcionar; se acrescentar qualquer coisa,
já não é mais o menor exemplo.

Converse dois minutos e repare em duas coisas:

1. Ele obedece à instrução (duas frases, sempre uma pergunta no fim).
2. Ele **inventa** com a maior tranquilidade. Pergunte o preço do dólar hoje.
   Ele não tem como saber e mesmo assim responde. Um agente sem ferramenta
   não tem de onde tirar o que não está no modelo.
"""

from google.adk.agents import Agent, SequentialAgent

from modelo import modelo

def hora_atual():
    from datetime import datetime 
    return datetime.now().strftime("%H:%M:%S")

def data_atual():
    from datetime import datetime 
    return datetime.now().strftime("%Y-%m-%d")

def soma_um(numero: int) -> int:
    """Soma 1 a um número inteiro."""
    return numero + 1

def soma(a: int, b: int) -> int:
    """Soma dois números inteiros."""
    return a + b

texto = "Cantor Rick morre após queda de helicóptero em Santa Catarina"

def ler_texto() -> str:
    """Textos sobre notícias atuais"""
    return texto

professor = Agent(
    name="professor",
    model=modelo(),
    description="Conversa sobre qualquer assunto, em duas frases por vez.",
    instruction=(
        "Você é um professor de computação que odeia resposta comprida. "
        "Responda SEMPRE em no máximo duas frases. "
        "Termine SEMPRE devolvendo uma pergunta curta para a pessoa. "
        "Se não souber, diga que não sabe — não invente."
        "{pergunta}"
    ),
    tools=[soma, hora_atual, data_atual, ler_texto]
)

analfabeto = Agent(
    name="analfabeto",
    model=modelo(),
    description="Faz perguntas óbvias sobre TI.",
    instruction=(
        "Faça perguntas sobre TI. Perguntas óbvias."
    ),
    tools=[soma, hora_atual, data_atual, ler_texto]
    ,output_key="pergunta"
)

root_agent = SequentialAgent(
    name="conversa",
    sub_agents = [analfabeto, professor],
)