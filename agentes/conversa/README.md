# `conversa`

O menor agente possível: um modelo, um nome, uma descrição e uma instrução.
Sem ferramenta, sem laço, sem segundo agente.

## A ideia

Um agente **é** um modelo com uma instrução. Nada mais. Se você tirar qualquer
uma das quatro linhas de `Agent(...)`, ele para; se acrescentar qualquer coisa,
já não é mais o menor exemplo.

## O que reparar ao conversar

1. Ele obedece à instrução (duas frases, sempre uma pergunta no fim).
2. Ele **inventa** com tranquilidade. Pergunte o preço do dólar hoje: ele não
   tem como saber e mesmo assim responde. Um agente sem ferramenta não tem
   de onde tirar o que não está no modelo.

## Rodar

```bash
just cli conversa
# ou: just web  → escolha "conversa" na lista
```

Detalhe no cabeçalho de [`agent.py`](agent.py). Contexto do curso no
[`README`](../../README.md) da raiz.
