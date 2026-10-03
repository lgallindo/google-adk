# `08_paralelo`

Três pareceristas no mesmo instante sobre um pedido real da CGU; um relator
costura. Amostra em [`dados/`](dados/).

```
SequentialAgent "paralelo"
├── porteiro
├── ParallelAgent "pareceres"
│   ├── juridico → parecer_juridico
│   ├── merito   → parecer_merito
│   └── risco    → parecer_risco
└── relator
```

## Por que esta pasta existe

Ângulos independentes sobre o mesmo texto pedem largada conjunta. Cada um
lê o `{pedido}` escrito antes do bloco; o relator é quem costura depois.
O gabarito `houve_recurso` fica fora das ferramentas do modelo —
`just gabarito <protocolo>`. Meça tempo com `just cronometro`.

## Rodar

```bash
just cli 08_paralelo
```
