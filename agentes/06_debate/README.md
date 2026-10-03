# `06_debate`

Três debatedores em laço, duas rodadas, um mediador. Sete chamadas ao modelo.

## Por que esta pasta existe

Orquestrar agentes multiplica custo e latência num desenho que a tela trata
como um único chat. Eles falam por `output_key` no estado da sessão; na
segunda rodada a chave é regravada. O tema é o que a pessoa digitar.

## Rodar

```bash
just cli 06_debate
```
