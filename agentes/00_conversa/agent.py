"""00_conversa — a primeira conversa com um agente.

Imagine que você acabou de ligar um microfone para um modelo de linguagem.
Nesta pasta o microfone é o ADK: um `Agent` com nome, descrição, instrução e
modelo. Quatro campos. A conversa começa.

O que esta pasta existe para mostrar é exatamente isso — o núcleo. Tudo o que
vier nas pastas seguintes (ferramentas, rede, grafos, debates) parte deste
mesmo objeto. Aqui ele aparece sozinho, para você sentir o comportamento cru:
ele segue a instrução; quando a pergunta pede um fato do mundo real, ele
responde com a mesma segurança de quem sabe — porque a única fonte dele é o
próprio modelo.

    just web            # escolha 00_conversa
    just cli 00_conversa
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
        "Se não souber, diga que não sabe — inventar custo caro depois."
    ),
)
