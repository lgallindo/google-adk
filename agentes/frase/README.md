# Variante 4d — `frase`

`ParallelAgent` no osso. Você cola **uma frase**, três agentes a reescrevem ao
mesmo tempo para três leitores diferentes, e um relator compara.

```
SequentialAgent "frase"
├── ParallelAgent "versoes"     ← as três ao mesmo tempo
│   ├── simples   português claro, para qualquer pessoa
│   ├── formal    registro de documento oficial
│   └── curta     no máximo 12 palavras
└── relator                     compara e aponta onde divergiram
```

Quatro chamadas ao modelo por frase.

## Para que serve

É a [`paralelo`](../paralelo/) sem nada em volta: **sem ferramenta, sem
arquivo de dados, sem gabarito, sem protocolo para decorar**. O que entra é a
frase que você colar; o que sai são três versões dela. Serve para mostrar
`ParallelAgent` com a turma olhando, sem que ninguém precise entender o
domínio antes.

Se quiser a mesma ideia num problema de verdade, com dados reais e um
gabarito para conferir, é a [`paralelo`](../paralelo/) que você quer.

## Rodar

```bash
just cli frase             # ou: just web → escolha "frase"
```

Cole uma frase e aperte enter. Tem frases prontas em
[`frases.md`](frases.md) — pode projetar, não tem nada escondido lá.

## A ideia

Os três **não se escutam**. Começam no mesmo instante, então nenhum lê o que o
outro escreveu; cada um vê só a sua instrução e a frase que você colou. Numa
fila (`SequentialAgent`), o segundo leria a escolha do primeiro e iria atrás.

## O que reparar — e um aviso

As três versões aparecem quase juntas, não uma a uma. Medido com o Gemini:
5,1s · 5,9s · 6,4s, sobrepostas, em vez de somadas.

**Não prometa divergência.** A tentação é dizer à turma "vejam, cada um vai
entender a frase ambígua de um jeito". Testado, não é o que acontece: em "Vi
o homem no morro com o telescópio" os três leram o telescópio como
instrumento de quem vê, e nenhum cogitou que o homem o carregava.

O resultado real é mais interessante que o prometido: **três agentes que não
se falaram chegaram à mesma leitura, porque compartilham o mesmo viés de
treino.** Independência de execução não produz diversidade de opinião. Vale a
pena dizer isso em voz alta, porque é o erro de projeto de quem monta um
comitê de agentes esperando que eles se corrijam.

Para divergência quase garantida, use o grupo D de `frases.md`: o limite de
12 palavras força o `curta` a descartar algo que os outros guardaram.

## Se o modelo demorar

Na cota gratuita do AI Studio um agente às vezes leva 60s em vez de 6s. Não é
o `ParallelAgent`: é o `HttpRetryOptions` de [`modelo.py`](../modelo.py)
repetindo um 429 ou 503 em silêncio. Rodando de novo costuma passar.

## Um aviso que vai aparecer na tela

```
DeprecationWarning: ParallelAgent is deprecated in favor of Workflow
```

Vale para `SequentialAgent` e `LoopAgent` também. Na 2.x os três viraram
legado em favor do [`Workflow`](https://adk.dev/graphs/) — é o que a variante
[`fluxo`](../fluxo/) usa. Nada quebra; é o jeito clássico, não o novo.

Detalhe no cabeçalho de [`agent.py`](agent.py). Contexto do curso no
[`README`](../../README.md) da raiz.
