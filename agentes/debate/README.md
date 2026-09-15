# Variante 4 — `debate`

Três agentes debatem; um quarto julga. O `root_agent` **não é um modelo**: é um
`SequentialAgent` com um `LoopAgent` (três debatedores × **duas** rodadas) e um
mediador.

```
SequentialAgent "debate"
├── LoopAgent "rodadas"  (max_iterations=2)
│   ├── otimista → state["arg_otimista"]
│   ├── cetico   → state["arg_cetico"]
│   └── pragmatico → state["arg_pragmatico"]
└── mediador
```

**Sete** chamadas ao modelo por pergunta — sete vezes o custo de
[`conversa`](../conversa/), e nada na tela avisa.

## Como os agentes conversam

Por `output_key` + `{chave}` na instrução. É variável compartilhada.

O laço **sobrescreve**. Na rodada 2 a fala da rodada 1 some do estado. O
mediador recebe só a última rodada pelas chaves; as anteriores só pelo
histórico da conversa. Esses defeitos de estado são o assunto da variante
[`ata`](../ata/).

## Rodar

```bash
just cli debate
# ou: just web  → escolha "debate"
```

Exercício: mude `max_iterations` de 2 para 1 e compare custo e qualidade.
