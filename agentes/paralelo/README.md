# Variante 4c — `paralelo`

Três pareceristas analisam **o mesmo pedido de acesso à informação, ao mesmo
tempo**, e um relator costura. O pedido é real: vem de uma amostra de 60
pedidos de 2025 da base do FalaBR da CGU (veja [`dados/`](dados/)).

```
SequentialAgent "paralelo"
├── porteiro                       busca o pedido  -> state["pedido"]
├── ParallelAgent "pareceres"      ← os três disparam juntos
│   ├── juridico   a decisão se sustenta na LAI?   -> parecer_juridico
│   ├── merito     a resposta responde?            -> parecer_merito
│   └── risco      a pessoa vai recorrer?          -> parecer_risco
└── relator                        lê os três e fecha
```

Cinco chamadas ao modelo por pedido.

## A ideia

**Eles não se escutam.** No [`debate`](../debate/), o cético interpola
`{arg_otimista}` e lê a fala da colega. Aqui isso não tem como funcionar: os
três começam no mesmo instante, então quando o jurídico monta o prompt dele o
parecer de mérito ainda não existe.

Repare no que eles **conseguem** ler: `{pedido}`, que o porteiro escreveu
antes do bloco paralelo. Estado escrito antes da largada todo mundo enxerga;
estado escrito dentro do bloco, ninguém. A fronteira é o instante em que o
`ParallelAgent` dispara.

E `ParallelAgent` não resume nada — ele dispara e espera. Quem costura é o
agente seguinte na sequência. Esse par fan-out/fan-in é o desenho padrão, e é
por isso que `ParallelAgent` quase nunca aparece sozinho.

## Rodar

```bash
just cli paralelo          # ou: just web → escolha "paralelo"
```

Peça, por exemplo:

> *Analise o pedido 50001121584202581.*
> *Sorteie um pedido com acesso negado.*
> *O que tem nessa amostra?*

## O gabarito

Cada pedido da amostra sabe se a pessoa **recorreu de verdade**. O parecerista
de `risco` tem que adivinhar isso sem ver: `pedidos.py` remove o campo antes
de entregar o pedido ao modelo. Depois, confira:

```bash
just gabarito 50001121584202581
just amostra                       # o que tem na amostra
```

A amostra está em 30 com recurso e 30 sem, então **o piso é 50%**: quem chuta
"vai recorrer" para tudo acerta metade. É contra esse piso que o parecer de
risco tem que ser comparado, e é o exercício mais honesto da pasta — rode uns
dez pedidos, anote o `RISCO:` de cada um, confira o gabarito e conte.

## O que reparar

1. Na interface web, os três pareceres aparecem quase juntos, não um a um.
2. Nenhum parecerista menciona o outro. Se algum mencionar, ele inventou.
3. O relator às vezes acha contradição onde não há. "A negativa é legal" e "a
   resposta não responde" podem ser verdade ao mesmo tempo, e ele foi
   instruído a reparar nisso. Às vezes obedece.
4. Modelo pequeno (Qwen3-0.6B) costuma errar o formato da linha `RISCO:`.
   Vale mostrar: instrução de formato é pedido, não garantia.

## Medir, em vez de acreditar

```bash
just cronometro                       # Gemini — ganho perto de 3×
ADK_BACKEND=qwen3 just cronometro     # Qwen3 local — empate
```

Monta o mesmo trio duas vezes, uma em `SequentialAgent` e outra em
`ParallelAgent`, dá o mesmo pedido aos dois e cronometra. Gasta 6 chamadas.

O empate no Qwen local é o ponto: `servico-qwen/` é um processo só, gerando
token a token na CPU, então as três chamadas chegam juntas e entram numa fila
mesmo assim. **`ParallelAgent` paraleliza a espera, não a conta.** Paralelo no
seu código só vira paralelo de verdade se o outro lado também for.

## Um aviso que vai aparecer na tela

```
DeprecationWarning: ParallelAgent is deprecated in favor of Workflow
```

Vale para `SequentialAgent` e `LoopAgent` também. Na 2.x os três viraram
legado em favor do [`Workflow`](https://adk.dev/graphs/), que é um grafo de
`edges` — é o que a variante [`fluxo`](../fluxo/) usa. Nada quebra, e a maior
parte do material que existe hoje ainda usa estas classes, mas é o jeito
clássico, não o novo.

## Arquivos

| Arquivo | O que é |
| --- | --- |
| [`agent.py`](agent.py) | Os cinco agentes e a montagem. |
| [`pedidos.py`](pedidos.py) | Carrega a amostra e expõe as 3 ferramentas do porteiro. |
| [`cronometro.py`](cronometro.py) | Mede fila × paralelo. |
| [`dados/`](dados/) | A amostra, a procedência e o script que a regera. |

Detalhe no cabeçalho de [`agent.py`](agent.py). Contexto do curso no
[`README`](../../README.md) da raiz.
