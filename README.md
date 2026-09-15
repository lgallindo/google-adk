# Agentes com o ADK do Google

Este repositório existe para **experimentar com o Agent Development Kit (ADK)
do Google** — a biblioteca que a gente usa para montar agentes: modelos de
linguagem que decidem sozinhos quando chamar uma função sua.

São cinco variantes e uma emenda. Cada variante é um agente inteiro, e a
diferença entre uma e a seguinte é **uma ideia só**. Leia na ordem; cada
`agent.py` explica no cabeçalho o que mudou em relação ao anterior. A `4b` é a
exceção: ela não traz ideia nova de agente, ela conserta os defeitos de estado
que a `4` deixa à mostra.

| # | Pasta | A ideia nova | Chamadas ao modelo |
| --- | --- | --- | --- |
| 1 | [`agentes/conversa`](agentes/conversa/agent.py) | Um agente é um modelo com uma instrução. Nada mais. | 1 |
| 2 | [`agentes/ferramenta`](agentes/ferramenta/agent.py) | Ferramenta é uma função Python — nove delas. A docstring vira a especificação. | 1 |
| 3 | [`agentes/externa`](agentes/externa/agent.py) | A ferramenta sai da máquina e chama uma API de verdade. | 1 |
| 4 | [`agentes/debate`](agentes/debate/agent.py) | Três agentes debatem 2 rodadas; um quarto julga. | **7** |
| 4b | [`agentes/ata`](agentes/ata/agent.py) | O mesmo debate, com as rodadas guardadas em ata em vez de sobrescritas. | **7** |
| 5 | [`adk-basico/`](adk-basico/README.md) | A ferramenta é um modelo de AM servido por HTTP, na própria pasta. | 1 |

A variante 5 mora em pasta separada, com ambiente próprio, porque precisa de
dois terminais e de bibliotecas que as outras cinco não usam. Ela é
autossuficiente: o modelo e o serviço que o expõe estão dentro dela.

---

## O que é o ADK

O ADK é uma biblioteca Python (também existe em Java e Go) de código aberto,
licença Apache 2.0, para escrever agentes. Ele cuida da parte chata e repetida:

- transformar uma função Python numa **ferramenta** que o modelo enxerga —
  lendo a assinatura e a docstring, sem você escrever schema JSON na mão;
- rodar o **laço** de conversa: o modelo pede uma ferramenta, o ADK executa,
  devolve o resultado, o modelo continua;
- guardar **sessão e estado** entre as mensagens;
- **orquestrar vários agentes** (em sequência, em paralelo, em laço), que é o
  que a variante `debate` usa;
- dar uma **interface web de teste** (`adk web`) e um modo terminal
  (`adk run`), que é como a gente roda tudo aqui.

O que o ADK **não** é: ele não é o modelo. Por padrão este repo usa **Qwen3
local** (`servico-qwen/`). Opcionalmente usa **Gemini** na nuvem
(`ADK_BACKEND=gemini` + chave). O ADK é só o código que fala com o modelo.

### Uma linha do tempo bem curta

| Quando | O que aconteceu |
| --- | --- |
| abr/2025 | O Google anuncia o ADK no Cloud Next, em Python, aberto. Junto vem o A2A, um protocolo para agentes de fabricantes diferentes conversarem. |
| mai/2025 | Sai a 1.0 do ADK Python, marcada como estável para produção, e a primeira versão em Java. |
| 2025–2026 | O ADK vira a base dos produtos de agente do próprio Google Cloud, ganha versão em Go, e passa por duas quebras de compatibilidade grandes (a 1.x e depois a 2.x). |
| hoje | Este repositório está preso na **2.8.0** (veja o `uv.lock`). |

Essa última linha importa mais do que parece. O ADK ainda muda rápido, e a
maior parte dos tutoriais que você vai achar no Google foi escrita para a 0.x
ou a 1.x — o código deles não roda aqui. Quando um exemplo da internet não
funcionar, **desconfie da versão antes de desconfiar de você**. É por isso que
o `uv.lock` existe e é por isso que ele está commitado.

### Para que servem agentes

O padrão é sempre o mesmo: quando o modelo sozinho não basta porque ele
precisa de um dado que não está nele, ou precisa **fazer** alguma coisa no
mundo. Alguns usos comuns:

- **Atendimento e triagem** — ler um pedido, consultar o sistema interno e
  decidir para onde mandar. É literalmente a variante 5 aqui: triagem de
  pedidos da LAI, com um modelo de AM como ferramenta.
- **Pesquisa e resumo** — buscar em várias fontes (busca, banco de dados,
  seus PDFs) e juntar num texto só.
- **Operações** — abrir chamado, agendar, mandar e-mail, consultar API —
  cada ação vira uma ferramenta.
- **Análise de dados em linguagem natural** — "quantos pedidos negados no
  trimestre?" vira uma consulta SQL executada por uma ferramenta.
- **Assistentes de código** — o Claude Code e o Cursor são agentes; as
  ferramentas deles são ler arquivo, editar arquivo e rodar comando.

E, sinceramente, um contra-exemplo: se a tarefa é sempre a mesma e você já sabe
a ordem dos passos, **um `if` resolve melhor e mais barato**. Agente serve
quando a ordem depende da pergunta.

---

## O que é o `uv`

O `uv` cuida do Python e das bibliotecas. Se você já penou com `pip`, `venv` e
`python -m venv`, ele faz o serviço dos três de uma vez só. Ele lê dois
arquivos que já estão na raiz do projeto — o `pyproject.toml`, que diz quais
bibliotecas são necessárias, e o `uv.lock`, que fixa a versão exata de cada
uma — e monta a pasta `.venv/` com esse conteúdo. Como o `uv.lock` fixa as
versões, a turma inteira acaba com o mesmo ADK, e o clássico "mas na minha
máquina funciona" perde a graça. Ele também baixa o próprio Python que este
projeto pede (3.12 ou mais novo), sem mexer no Python que já existe na sua
máquina.

Uma consequência prática: você **não precisa "ativar" ambiente nenhum**. As
receitas chamam `uv run`, que entra no `.venv/` do projeto sozinho, a cada
comando. É daí que vem o `--no-active` que você vai ver espalhado pelos
justfiles: ele manda o `uv` ignorar qualquer ambiente que você por acaso tenha
ativado na mão e usar sempre o `.venv/` deste projeto.

São **dois** ambientes aqui, e de propósito: um na raiz, para as cinco
pastas de `agentes/`, e outro dentro de `adk-basico/`, que precisa também do
BentoML e do scikit-learn. Cada um tem o seu `pyproject.toml` e o seu
`uv.lock`, e cada um pede o seu `just sync`.

---

## O que é o `just`

Todos os comandos deste projeto começam com a palavra `just`. O `just` é um
programinha que guarda comandos longos debaixo de nomes curtos: em vez de você
decorar e digitar `uv run --no-active adk web agentes`, você digita `just web`.
Esses apelidos ficam escritos num arquivo de texto comum chamado **justfile**,
que você pode abrir e ler — este projeto tem um na raiz e outro em
`adk-basico/`. Cada apelido é chamado de **receita**. O `just` não faz parte do
Python nem do ADK: é uma ferramenta separada, e existe só para você não
precisar decorar comando nenhum. A qualquer momento, rode `just` sozinho para
ver as receitas disponíveis.

---

## O que é uma chave de API (só se for usar Gemini)

O caminho **padrão** deste repo é Qwen3 local — **não precisa de chave**.

Gemini é opcional (`just web-gemini`). Aí sim: quando o agente "pensa", o ADK
faz HTTP para o Google. A **chave de API** identifica a sua conta e a cota.

1. **Chave é senha.** Não cole em slide, WhatsApp da turma, nem no git. Mora
   em `.env` (gitignored); no git só existe `.env.exemplo`.
2. **Sem chave válida, só o caminho Gemini quebra** — o Qwen local continua
   normal.

### Pegando uma chave (opcional)

1. <https://aistudio.google.com/apikey> com Gmail **pessoal** (conta de
   faculdade/Workspace costuma bloquear).
2. Aceite os termos; **Create API key**.
3. **Key Type** = Authorization / auth key (não Standard).
4. Cole no `.env` e rode `just chave`.

Cota gratuita responde `429`/`503` quando aperta — ver "Por que a variante 4
é cara" e [`agentes/modelo.py`](agentes/modelo.py).

---

## Instalação

```bash
# uma vez na máquina
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install rust-just
sudo apt install jq   # se ainda não tiver
```

Confira: `uv --version && just --version && jq --version`  
(`just` ≥ 1.31; evite o `just` velho do `apt`.)

**Não faça `source …/bin/activate`.** As receitas usam `uv run --no-active`
e montam o `.venv` deste repo sozinhas. Se você ativar o venv de
`adk-basico/` ou de outra pasta de aula, o `adk` pode importar pacotes do
lugar errado.

**Dentro deste repositório:**

```bash
just sync                 # .venv do ADK
just sync-qwen            # .venv do servico-qwen (torch CPU + BentoML)
```

A variante 5 (`adk-basico/`) tem ambiente próprio — veja o README dela.

## Rodar (Qwen local — padrão)

Dois terminais:

```bash
just qwen-serve           # terminal 1 — modelo (porta 3000)
just web                  # terminal 2 — http://localhost:8000
```

Comece pela variante **conversa**. No terminal: `just cli conversa`.

Se a porta 3000 estiver ocupada:

```bash
PORT=3001 just qwen-serve
QWEN_API_BASE=http://127.0.0.1:3001/v1 just web
```

Smoke do modelo sem abrir o ADK: `just verificar-qwen`.

## Rodar com Gemini (opcional)

```bash
cp .env.exemplo .env      # cole a auth key do AI Studio
just chave
just web-gemini
# ou: just cli-gemini conversa
```

Antes de gastar cota na nuvem:

```bash
just verificar
just testar-api
```
## Por que a variante 2 existe

Isto foi medido em **09/09/2026**, com a mesma pergunta, no mesmo dia, com o
mesmo modelo. A única diferença é que a segunda tem uma ferramenta.

```
pergunta:  "Quantos dias faltam para 2026-09-24?"

conversa    -> "Faltam exatamente 668 dias para essa data."     ERRADO
ferramenta  -> "Faltam exatamente 15 dias para o dia 24/09."    CERTO
```

Repare que os **dois** disseram *"exatamente"*. O primeiro não tem como saber
que dia é hoje, não sabe que não sabe, e responde com a mesma segurança do
segundo. Não existe nada na resposta errada que a denuncie.

É a mesma lição que `~/bentoml-roberta/api/` mostra do outro lado: lá o modelo
de QA responde *"terça-feira"* para uma pergunta de *"quando"*, com score
**maior** que o das respostas certas. Modelo confiante e modelo correto são
coisas diferentes, e nenhum painel de servidor distingue as duas.

## Por que a variante 4 é cara

Sete chamadas por pergunta: 3 debatedores × 2 rodadas + 1 mediador. Isso é
**sete vezes** o custo e a latência da variante 1, e nada na tela avisa.

E não é só custo. Medido no mesmo dia, seis chamadas seguidas a
`gemini-3.1-flash-lite` na cota gratuita deram **3 sucessos e 3 erros 503**. Com
50% de falha por chamada, a chance de as sete passarem é 0,5⁷ — cerca de uma em
128. **O debate falhou** na prática antes de existir o
[`agentes/modelo.py`](agentes/modelo.py), que liga repetição automática em
429/500/502/503/504 com espera que dobra a cada tentativa.

A conta vale além do Gemini: **num sistema de N passos em série, a
confiabilidade de cada passo entra elevada a N.** Encadear agentes multiplica a
fragilidade tão rápido quanto multiplica o custo. Repetição compra resiliência
contra falha transitória — não contra indisponibilidade.

## O que a variante 4b conserta

A `debate` funciona, e é justamente por funcionar que ela ensina: os três
defeitos dela são de **estado**, e nenhum deles aparece na resposta.

O mecanismo é o `output_key`. Cada debatedor grava a própria fala numa chave da
sessão (`arg_otimista`, `arg_cetico`, `arg_pragmatico`) e os outros leem aquela
chave interpolando `{arg_otimista}` na instrução. Funciona como variável
compartilhada — e tem os problemas de uma variável compartilhada:

1. **O laço sobrescreve.** `output_key` atribui, não acrescenta. Na rodada 2 o
   otimista regrava a própria chave e a fala da rodada 1 sai do estado. Ao
   final das duas rodadas, o estado tem três falas — as últimas. As outras três
   existiram e não estão em lugar nenhum que você possa abrir.
2. **O mediador julga o que não leu.** Pelas chaves ele recebe só a rodada 2.
   A primeira chega a ele pelo histórico da conversa, que é uma coisa
   que ele vê mas que você não monta, não inspeciona e não controla.
3. **A leitura é assimétrica.** O otimista não tem nenhum `{...}` na
   instrução, o cético tem um, o pragmático tem dois. Os três debatem olhando
   para estados diferentes, e isso não está escrito em lugar nenhum — está
   implícito na ordem da lista de `sub_agents`.

A `ata` resolve os três com duas peças do ADK que a `debate` não usa:

- **`after_agent_callback`** — roda depois de cada debatedor, na janela em que
  a fala já está na chave e a próxima rodada ainda não a sobrescreveu. Ele
  copia a fala para o fim de uma lista em `state["ata"]`. Seis falas ao final,
  com rodada e autor. O `output_key` deixa de ser a memória do debate e passa a
  ser só a caixa de entrada do callback.
- **instrução que é função** — `instruction=` aceita uma string ou um callable
  que recebe o contexto e devolve o texto. Uma lista não cabe na forma string
  (`{ata}` renderizaria o `repr` do Python no prompt), então a transcrição é
  montada com um `for`. Os três debatedores usam a **mesma** função, e a
  assimetria desaparece.

Duas armadilhas que valem a aula, as duas anotadas no código:

- `state["ata"] = nova_lista` registra a mudança; `state["ata"].append(...)`
  **não**. Com sessão em memória os dois parecem funcionar, porque é o mesmo
  objeto. O segundo só quebra no dia em que você liga o banco.
- O contador de rodada mora num `before_agent_callback` do otimista **porque
  ele é o primeiro da lista**. Troque a ordem dos `sub_agents` e o contador
  precisa mudar de agente junto.

O custo não muda: continuam sete chamadas. O que aumenta é o **número de
tokens** — a ata viaja no prompt de todo mundo e o histórico da conversa
continua viajando também.

E um defeito que a `4b` não conserta, porque não é dela: o estado morre com o
processo. Quem escolhe onde guardar sessão não é o `agent.py`, é quem sobe o
servidor. `just web` usa memória; `just web-memoria` sobe o mesmo servidor com
um SQLite ao lado, e aí a ata sobrevive a um Ctrl+C.

## O que dá para mexer em aula

- **`conversa`** — mude a instrução e veja o comportamento mudar sem tocar em código.
- **`ferramenta`** — apague a linha `data:` do bloco `Args` da docstring e veja o
  agente começar a errar o formato. A docstring **é** a especificação.
  Peça também *"anote isso no seu arquivo"* e depois *"apague tudo"*: é a
  única ferramenta das nove que **muda** alguma coisa na sua máquina, e nada
  na tela pede confirmação.
- **`externa`** — desligue o wi-fi e veja a ferramenta devolver `{"erro": ...}`
  em vez de derrubar o turno.
- **`debate`** — mude `max_iterations` de 2 para 1 e compare custo e qualidade.
  Ou acrescente um quarto debatedor e veja quantas chamadas isso vira.
- **`ata`** — rode a mesma pergunta nas duas e abra a aba **State** do
  `adk web` lado a lado: a `debate` termina com três falas guardadas, a `ata`
  com seis. Depois comente o `after_agent_callback=registrar` de um dos três e
  veja a ata ficar com furo — sem nenhum erro na tela.

## Onde isto encosta no resto do curso

`agentes/externa` e `~/bentoml-roberta/api/` usam **a mesma** BrasilAPI de dois
jeitos diferentes: o agente **chama** a API e lê o JSON; o serviço de QA
transforma o JSON em prosa e **grifa** a resposta dentro do texto. Mesma fonte,
duas arquiteturas, dois modos de errar. Vale abrir os dois lado a lado.

## Quando algo dá errado

| Mensagem | O que fazer |
|---|---|
| `ERRO: não existe .env aqui` | rode `cp .env.exemplo .env`, cole a chave, e `just chave` de novo |
| `ERRO: o .env ainda tem o texto de exemplo` | você copiou o arquivo mas não colou a chave dentro dele |
| `401`, `PERMISSION_DENIED`, `API key not valid` | chave errada, com espaço sobrando, não copiada (`just chave`), chave **Standard** (crie uma **auth key** nova no AI Studio), ou conta institucional sem permissão de criar chave — use Gmail pessoal |
| `429 RESOURCE_EXHAUSTED` | você bateu na cota gratuita. Espere um minuto |
| `503 ... high demand` | o servidor recusou. O `modelo.py` já repete sozinho; se insistir, espere |
| `adk: command not found` | você rodou fora do `uv run`. Use as receitas do `just` |
| A interface web não abre | ela sobe em <http://localhost:8000>, e o terminal fica ocupado enquanto ela está de pé |
| `ERRO: Qwen não responde` | `just qwen-serve` noutro terminal; espere carregar; depois `just web` |
| `LiteLLM support requires: google-adk[extensions]` | o `.venv` estava quebrado (shebang apontava para outra aula) ou você ativou outro venv. Rode `deactivate`, depois `rm -rf .venv && just sync`. **Não** use `source …/activate` |
| porta 3000 ocupada | `PORT=3001 just qwen-serve` e `QWEN_API_BASE=http://127.0.0.1:3001/v1 just web` |
| Qwen lento / máquina pesada | normal em CPU com `debate`/`ata` (7 chamadas); use `conversa` ou `just web-gemini` |
