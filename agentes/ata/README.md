# Variante 4b — `ata`

O mesmo debate de [`debate`](../debate/): três debatedores, **duas** rodadas, um
mediador, **sete** chamadas. O que muda é **o que sobra no estado** quando
acaba.

## O que a `debate` deixa à mostra (e isto conserta)

1. **`output_key` sobrescreve** — a fala da rodada 1 some na rodada 2.
   → `after_agent_callback` (`registrar`) copia cada fala para o fim de
   `state["ata"]`. Seis falas ao final, com rodada e autor.
2. **O mediador julga o que não leu pelas chaves** — só a última rodada.
   → Ele lê a ata inteira, montada em Python, visível na aba **State**.
3. **Leitura assimétrica** — otimista sem `{...}`, cético com um, pragmático
   com dois.
   → Os três usam a **mesma** função de instrução e a mesma transcrição.

## Ferramenta nova: instrução que é função

`instruction=` aceita string **ou** callable. Uma lista não cabe em
`{ata}` (viraria o `repr` do Python), então a transcrição é montada com um
`for`. Com função, o ADK **não** interpola `{}` no resultado.

Armadilha: `state["ata"] = nova_lista` registra a mudança;
`state["ata"].append(...)` **não** (quebra quando a sessão vai para o banco).

## O que esta variante não conserta

O estado ainda morre com o processo se o servidor for em memória.
`just web-memoria` grava sessão num SQLite (`sessoes.db`) e a ata sobrevive a
um Ctrl+C.

## Rodar

```bash
just cli ata
# ou: just web  → escolha "ata"
```
