# Agentes

Cada subpasta é um agente completo e se explica sozinha. A numeração
(`00` … `09`) sobe com a **complexidade do código**. Nomes usam `_` (o ADK
aceita só `[A-Za-z0-9_]` em pastas de agente).

| Pasta | Razão de ser |
| --- | --- |
| [`00_conversa/`](00_conversa/) | Ligar o microfone: um modelo, uma instrução, uma conversa. |
| [`01_ferramenta/`](01_ferramenta/) | Dar mãos ao modelo — funções Python viram ferramentas. |
| [`02_externa/`](02_externa/) | A ferramenta sai da máquina e fala com a BrasilAPI. |
| [`03_fluxo/`](03_fluxo/) | Orquestração como grafo: dois nós, uma corrente. |
| [`04_frase/`](04_frase/) | Uma frase, três reescritas no mesmo instante. |
| [`05_fontes/`](05_fontes/) | Abrir em leque, esperar na barreira, costurar. |
| [`06_debate/`](06_debate/) | Três vozes em laço; um mediador fecha. |
| [`07_ata/`](07_ata/) | O debate com cada fala guardada em ata. |
| [`08_paralelo/`](08_paralelo/) | Pareceristas juntos sobre um pedido real da CGU. |
| [`09_pesquisa/`](09_pesquisa/) | Pipeline de pesquisa com dois abre-e-fecha. |

O [`../adk-basico/`](../adk-basico/README.md) fica fora da numeração: ambiente
próprio (BentoML + modelo tabular como ferramenta).

## Arquivos desta pasta

| Arquivo | Função |
| --- | --- |
| [`modelo.py`](modelo.py) | Gemini por padrão; opcional `ADK_BACKEND=local`. |
| `*/agent.py` | O ADK procura `root_agent` neste arquivo. |
| `*/.env` | Chave Gemini (`just chave` na raiz). |

## Rodar

```bash
just sync
cp .env.exemplo .env   # cole a chave do AI Studio
just chave
just web               # http://localhost:8000
# ou: just cli 00_conversa
```
