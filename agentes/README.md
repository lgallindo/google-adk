# Agentes — cinco variantes

Cada subpasta é um agente completo. A diferença entre uma e a seguinte é
**uma ideia só**. Leia na ordem; o cabeçalho de cada `agent.py` explica o que
mudou.

| # | Pasta | A ideia nova | Chamadas ao modelo |
| --- | --- | --- | --- |
| 1 | [`conversa/`](conversa/) | Um agente é um modelo com uma instrução. | 1 |
| 2 | [`ferramenta/`](ferramenta/) | Ferramenta é uma função Python — a docstring vira a especificação. | 1 |
| 3 | [`externa/`](externa/) | A ferramenta sai da máquina e chama uma API de verdade. | 1 |
| 4 | [`debate/`](debate/) | Três agentes debatem 2 rodadas; um quarto julga. | **7** |
| 4b | [`ata/`](ata/) | O mesmo debate, com as rodadas guardadas em ata. | **7** |
| 4c | [`paralelo/`](paralelo/) | Três pareceristas ao mesmo tempo, sobre pedidos de LAI reais; eles não se escutam. | **5** |
| 4d | [`frase/`](frase/) | O mesmo paralelo no osso: cole uma frase, três versões ao mesmo tempo. | **4** |

A variante 5 mora em [`../adk-basico/`](../adk-basico/README.md), com ambiente
próprio.

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
