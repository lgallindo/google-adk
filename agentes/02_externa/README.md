# `02_externa`

Mesma forma de ferramenta — docstring, tipos, `tools=[...]` — e as funções
fazem HTTP na [BrasilAPI](https://brasilapi.com.br).

## Por que esta pasta existe

A rede traz timeout, 403, 500, DNS e JSON inesperado. As ferramentas desta
pasta devolvem `{"erro": ...}` e o turno segue: o modelo explica o problema.
Os cabeçalhos no código existem porque a BrasilAPI responde 403 ao
User-Agent padrão do `urllib`.

## Rodar

```bash
just cli 02_externa
```
