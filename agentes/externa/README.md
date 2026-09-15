# Variante 3 — `externa`

Mesma estrutura de [`ferramenta`](../ferramenta/): funções + `tools=[...]`.
Aqui as funções fazem HTTP para a [BrasilAPI](https://brasilapi.com.br)
(aberta, sem chave).

## A ideia

Do ponto de vista do agente, somar dois números e atravessar a internet são a
mesma coisa. Isso é simples — e perigoso: o modelo não sabe que aquilo custa
rede.

## O que muda é o que pode dar errado

Função local falha com exceção. Função externa falha com timeout, 403, 500,
DNS, formato inesperado. As ferramentas desta pasta **devolvem
`{"erro": ...}`** em vez de estourar: exceção derruba o turno; erro devolvido
deixa o modelo explicar o problema.

A BrasilAPI responde 403 para o User-Agent padrão do `urllib` — por isso há
cabeçalhos customizados no código.

## Ponte com o resto do curso

`~/bentoml-roberta/api/` usa a **mesma** API de outro jeito: lá os feriados
viram prosa e um modelo de QA grifa a resposta. Aqui o agente chama a API e lê
o JSON.

## Rodar

```bash
just testar-api           # a BrasilAPI responde? (sem gastar o modelo)
just cli externa
# ou: just web  → escolha "externa" na lista
```

Exercício em aula: desligue o wi-fi e veja `{"erro": ...}` em vez do turno
cair.

Detalhe no cabeçalho de [`agent.py`](agent.py).
