# Agentes

Cada subpasta é um agente completo e se explica sozinha: o cabeçalho do
`agent.py` diz o que aquela pasta faz e por que ela existe. A tabela abaixo é
só um índice, da mais simples para a mais cara.

| Pasta | A ideia | Chamadas ao modelo |
| --- | --- | --- |
| [`conversa/`](conversa/) | Um agente é um modelo com uma instrução. | 1 |
| [`ferramenta/`](ferramenta/) | Ferramenta é uma função Python — a docstring vira a especificação. | 1 |
| [`externa/`](externa/) | A ferramenta sai da máquina e chama uma API de verdade. | 1 |
| [`debate/`](debate/) | Três agentes debatem 2 rodadas; um quarto julga. | **7** |
| [`ata/`](ata/) | Um debate de duas rodadas, com as falas guardadas em ata. | **7** |
| [`paralelo/`](paralelo/) | Três pareceristas ao mesmo tempo, sobre pedidos de acesso à informação reais; eles não se escutam. | **5** |
| [`frase/`](frase/) | `ParallelAgent` no osso: cole uma frase, três versões ao mesmo tempo. | **4** |

O [`../adk-basico/`](../adk-basico/README.md) mora em pasta separada, com
ambiente próprio.

## Arquivos desta pasta

| Arquivo | Função |
| --- | --- |
| [`modelo.py`](modelo.py) | **Qwen3 local** por padrão; Gemini se `ADK_BACKEND=gemini`. |
| `*/agent.py` | O agente em si. O ADK procura `root_agent` neste arquivo. |
| `*/.env` | Só para Gemini (`just chave`). |

## Rodar

Da raiz:

```bash
just sync && just sync-qwen   # uma vez
just qwen-serve               # terminal 1
just web                      # terminal 2 → http://localhost:8000
```

Contexto no [`README.md`](../README.md) da raiz.
