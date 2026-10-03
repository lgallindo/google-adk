# `01_ferramenta`

Funções Python na lista `tools=[...]`. O ADK monta a oferta ao modelo a
partir do nome, dos tipos e da docstring.

## Por que esta pasta existe

Quando a pergunta pede conta, relógio ou arquivo, o modelo sozinho chuta.
Aqui quem calcula é o Python; o modelo decide **quando** chamar e **com
quais** argumentos. Apague a linha `data:` do `Args` de `dias_ate` e o
formato da data começa a falhar — a docstring é a especificação.

## Duas famílias

| Só respondem | Escrevem na máquina |
| --- | --- |
| `dias_ate`, `sortear`, `data_de_hoje`, `hora_agora`, `pasta_atual`, `listar_arquivos`, `nome_do_computador`, `ler_arquivo` | `escrever_arquivo` → `arquivo_do_agente.md` |

## Rodar

```bash
just cli 01_ferramenta
```
