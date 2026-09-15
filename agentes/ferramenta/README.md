# Variante 2 — `ferramenta`

A diferença para [`conversa`](../conversa/) são funções Python e a linha
`tools=[...]`. Não há registro de ferramentas, nem schema JSON escrito à mão.

## A ideia

Ferramenta é uma função. O ADK monta a descrição a partir do nome, dos tipos e
da docstring. Medido no ADK 2.8.0: a docstring inteira (bloco `Args:`
incluído) vira a descrição; o schema leva só nomes e tipos.

Mude a docstring e o comportamento muda **sem tocar no modelo**. Exercício:
apague a linha `data:` do bloco `Args` e veja o agente errar o formato da data.

## O que isto conserta

Em `conversa` o agente inventava contas e não sabia que dia era hoje. Aqui quem
conta é Python e quem olha o relógio é o SO. O modelo só decide **quando**
chamar e **com quais** argumentos.

## Duas famílias de ferramenta

| Só respondem | Mexem na máquina |
| --- | --- |
| `dias_ate`, `sortear`, `data_de_hoje`, `hora_agora`, `pasta_atual`, `listar_arquivos`, `nome_do_computador`, `ler_arquivo` | `escrever_arquivo` |

Peça *"anote isso no seu arquivo"* e depois *"apague tudo"*: nada na tela pede
confirmação.

## Rodar

```bash
just cli ferramenta
# ou: just web  → escolha "ferramenta" na lista
```

Detalhe no cabeçalho de [`agent.py`](agent.py).
