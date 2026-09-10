# Um agente, em 46 linhas

O agente não é o modelo. O agente é um **modelo de linguagem que sabe chamar funções
suas** — e uma dessas funções, aqui, é um modelo de aprendizado de máquina servido por
HTTP.

Esta pasta é **autossuficiente**. O modelo (`servico/modelo.joblib`) e o serviço que o
expõe (`servico/service.py`) estão aqui dentro. Você não precisa de nenhuma outra pasta.

## Instalar

```
just sync
cp .env.exemplo triagem/.env
```

Depois abra `triagem/.env` e cole sua chave do Google AI Studio:
<https://aistudio.google.com/apikey>

## Rodar

Precisa de **duas coisas de pé**. Em um terminal, o serviço:

```
just servico
```

Confira que ele respondeu, antes de gastar chamada ao modelo:

```
just testar-servico
```

```
Acesso Negado    -> {"risco_de_recurso": 0.6976}
Acesso Concedido -> {"risco_de_recurso": 0.4296}
```

Em outro terminal, o agente:

```
just web
```

Abra <http://localhost:8000>, escolha `triagem` na lista e pergunte:

> *A ouvidoria tem 32 mil pedidos na fila e consegue revisar 10%. Um pedido do
> Ministério da Saúde teve Acesso Negado — vale revisar?*

Ele vai chamar **as duas** ferramentas e juntar as respostas.

## O `agent.py` inteiro

Três blocos, e nada além disso:

```python
def risco_de_recurso(orgao: str, decisao: str) -> dict:
    """Estima o risco de um pedido da LAI virar recurso.

    Args:
        orgao: nome do órgão destinatário, por exemplo "Ministério da Saúde".
        decisao: a decisão dada ao pedido, por exemplo "Acesso Negado".
    """
```

1. **A ferramenta é uma função Python comum.** Não herda de nada, não tem decorador.
2. **A anotação de tipo e a primeira linha da docstring são o que o modelo lê.** Medido
   nesta versão (ADK 2.8.0), o schema que sai da função é exatamente este:

   ```json
   {"properties": {"orgao": {"title": "Orgao", "type": "string"},
                   "decisao": {"title": "Decisao", "type": "string"}},
    "required": ["orgao", "decisao"], "type": "object"}
   ```

   Olhe o que **não** está aí: as explicações do bloco `Args:`. Nesta versão elas
   **não chegam ao modelo** — só a primeira linha da docstring chega, como descrição da
   ferramenta. Então tudo que o modelo precisa saber para preencher um argumento tem que
   estar nessa primeira linha ou no **nome** do parâmetro. Nome de parâmetro é interface,
   não estilo.
3. **O agente é uma declaração:**

```python
root_agent = Agent(
    name="triagem",
    model=modelo(),
    description="Ajuda a ouvidoria a escolher quais pedidos da LAI revisar.",
    instruction="...",
    tools=[risco_de_recurso, orcamento_de_revisao],
)
```

Quem decide **qual** ferramenta chamar, com **quais** argumentos, e em que **ordem**, é o
modelo — em tempo de execução, a partir do que você perguntou. Você não escreveu nenhum
`if`.

## Por que `model=modelo()`, e não o nome do modelo

Porque a forma curta não repete a chamada quando o servidor recusa, e a cota gratuita
recusa com frequência: medido em 09/09/2026, seis chamadas seguidas a
`gemini-3.1-flash-lite` deram **3 sucessos e 3 erros 503**. Não se dá aula com 50% de
chance de a demonstração falhar na frente da turma. Ver
[`triagem/modelo.py`](triagem/modelo.py).

## A pergunta de monitoramento que esta pasta abre

O serviço em `servico/` não sabe que quem o chama é um agente. Do lado dele é um cliente
HTTP como qualquer outro — e é justamente aí que está o problema novo: agora existe um
cliente que chama o endpoint **quantas vezes quiser**, com argumentos que **você não
escolheu**, decididos por um modelo de linguagem em tempo de execução.

Duas coisas passam a valer a pena medir, e nenhuma delas aparece no painel de latência:

1. **Quantas chamadas por pergunta.** Uma pergunta do usuário pode virar zero, uma ou
   cinco chamadas ao seu modelo. Você não controla o número.
2. **Se a ferramenta foi chamada.** A instrução do agente diz *"nunca invente um risco sem
   chamar a ferramenta"*. Isso é uma afirmação **verificável**: conte as respostas que
   passaram pelo `/risco` e compare com as respostas dadas. A diferença é invenção.
