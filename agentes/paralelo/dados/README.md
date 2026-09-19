# `dados/` — 60 pedidos de LAI reais

## O que tem aqui

| Arquivo | O que é |
| --- | --- |
| `pedidos.jsonl` | A amostra. 60 pedidos, um por linha, ~150 KB. **Commitado.** |
| `baixar.py` | Baixa da CGU e regera o `pedidos.jsonl`. |
| `.cache/` | O zip de 82 MB da CGU. **Ignorado pelo git.** |

## Procedência

Portal de Dados Abertos da CGU, base do FalaBR — o sistema por onde entram os
pedidos de Lei de Acesso à Informação do Executivo federal:

<https://dadosabertos-download.cgu.gov.br/FalaBR/Arquivos_FalaBR_Filtrado/>

- **Arquivo de origem:** `Arquivos_csv_2025.zip` (82 MB), extração da CGU de
  15/09/2026.
- **Universo:** 83.827 pedidos concluídos em 2025. Destes, 51.480 passaram no
  filtro de tamanho de texto, e 60 foram sorteados.
- **Licença:** dados públicos, Lei 12.527/2011. Cite a CGU como fonte.
- **"Filtrado"** no nome do arquivo é da própria CGU: ela já removeu a
  identificação de quem pediu. O `baixar.py` ainda passa uma segunda vez
  tirando e-mail, CPF, CNPJ e telefone que tenham sobrado no texto livre —
  são 14 remoções nesta amostra.

## Por que a amostra não tem a proporção da base real

Na base, 74% dos pedidos são "Acesso Concedido". Uma amostra fiel teria quase
só concessão, e a aula ficaria sem o caso interessante. As cotas estão no topo
de `baixar.py`:

| Decisão | Na amostra | Na base 2025 |
| --- | --- | --- |
| Acesso Concedido | 18 | 74% |
| Acesso Parcialmente Concedido | 14 | 8% |
| Acesso Negado | 14 | 6% |
| Informação Inexistente | 6 | 4% |
| Órgão não tem competência | 4 | 2% |
| Não se trata de solicitação | 4 | 2% |

São 48 órgãos distintos. Diga isso à turma: **a amostra é enviesada de
propósito**, então nada que se meça aqui é estimativa de nada no mundo.

## O gabarito

Cada pedido traz `houve_recurso` e `qtd_recursos`, vindos do arquivo
`Recursos` da mesma extração, ligados por `IdPedido`. A amostra está
equilibrada em **30 com recurso e 30 sem**.

Isso é gabarito para o parecerista de `risco`, e ele nunca o vê:
`pedidos.py` remove os dois campos antes de entregar qualquer pedido ao
modelo. Confira depois, no terminal:

```bash
just gabarito 50001121584202581
```

O piso é 50%: quem chuta "vai recorrer" para todos acerta metade. Um parecer
de risco só vale alguma coisa se bater isso de forma consistente.

## Regerar

```bash
just dados                       # 2025, 60 pedidos
just dados --ano 2024 --n 120    # outro ano, outra amostra
```

O download tem cache: a segunda execução não baixa de novo. Para forçar,
apague `.cache/`.

## Campos de cada linha

| Campo | Vem de |
| --- | --- |
| `protocolo`, `orgao`, `esfera`, `data_registro` | identificação |
| `assunto`, `subassunto`, `resumo` | classificação dada pelo solicitante |
| `pedido` | `DetalhamentoSolicitacao` — o texto integral do que foi pedido |
| `data_resposta`, `resposta` | o que o órgão respondeu |
| `decisao`, `especificacao_decisao`, `detalhamento_decisao` | o desfecho |
| `motivo_negativa`, `foi_prorrogado` | só quando se aplicam |
| `houve_recurso`, `qtd_recursos` | **gabarito** — o modelo não recebe |
