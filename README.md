# Agentes com o ADK do Google

Este repositório existe para **experimentar com o Agent Development Kit (ADK)
do Google** — a biblioteca que a gente usa para montar agentes: modelos de
linguagem que decidem sozinhos quando chamar uma função sua.

São cinco variantes. Cada uma é um agente inteiro, e a diferença entre uma e a
seguinte é **uma ideia só**. Leia na ordem; cada `agent.py` explica no cabeçalho
o que mudou em relação ao anterior.

| # | Pasta | A ideia nova | Chamadas ao modelo |
| --- | --- | --- | --- |
| 1 | [`agentes/conversa`](agentes/conversa/agent.py) | Um agente é um modelo com uma instrução. Nada mais. | 1 |
| 2 | [`agentes/ferramenta`](agentes/ferramenta/agent.py) | Ferramenta é uma função Python — nove delas. A docstring vira a especificação. | 1 |
| 3 | [`agentes/externa`](agentes/externa/agent.py) | A ferramenta sai da máquina e chama uma API de verdade. | 1 |
| 4 | [`agentes/debate`](agentes/debate/agent.py) | Três agentes debatem 3 rodadas; um quarto julga. | **12** |
| 5 | [`adk-basico/`](adk-basico/README.md) | A ferramenta é um modelo de AM servido por HTTP, na própria pasta. | 1 |

A variante 5 mora em pasta separada, com ambiente próprio, porque precisa de
dois terminais e de bibliotecas que as outras quatro não usam. Ela é
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

O que o ADK **não** é: ele não é o modelo. O modelo (aqui, o Gemini) mora num
servidor do Google e é cobrado por chamada. O ADK é só o código que fala com
ele do seu lado.

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

São **dois** ambientes aqui, e de propósito: um na raiz, para as quatro
primeiras variantes, e outro dentro de `adk-basico/`, que precisa também do
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

## O que é uma chave de API, e como conseguir uma

O modelo não roda na sua máquina. Quando o agente "pensa", o que acontece de
verdade é uma requisição HTTP para um servidor do Google, que roda o Gemini e
devolve a resposta. A **chave de API** é o texto que vai junto nessa
requisição para dizer *quem* está pedindo: é ao mesmo tempo a sua identidade,
a sua permissão de uso e o endereço da conta que leva a cota — ou a fatura.

Duas consequências, e as duas valem para qualquer API paga, não só esta:

1. **Chave é senha.** Quem tem a sua chave gasta no seu nome. Não cole em
   slide, não mande no WhatsApp da turma, não commite. É por isso que aqui ela
   mora em arquivos `.env`, que não vão para o git — o que está commitado é o
   `.env.exemplo`, com o texto `cole-sua-chave-aqui` no lugar.
2. **Sem chave, nada roda.** Se você ver um erro falando em
   `GOOGLE_API_KEY`, `401` ou `PERMISSION_DENIED`, quase sempre é a chave
   faltando, com espaço sobrando, ou não copiada para a pasta da variante.

### Pegando a sua (é de graça)

1. Entre em <https://aistudio.google.com/apikey> com uma conta Google.
2. Clique em **Create API key** / *Criar chave de API*. Se ele pedir para
   escolher ou criar um projeto do Google Cloud, pode aceitar o que ele
   sugerir.
3. Copie o texto que aparece (começa com `AIza...`). Ele só é mostrado
   inteiro nessa hora — se perder, gere outra e apague a antiga.
4. Cole no `.env`, como está na seção de instalação abaixo.

O AI Studio tem uma **cota gratuita**, que é o que a turma usa. Ela é
suficiente para a aula, mas é limitada por minuto e por dia, e quando aperta o
servidor responde `429` ou `503` em vez da resposta. Isso não é bug seu — é
justamente o assunto da seção "Por que a variante 4 é cara", mais abaixo, e o
motivo de existir o [`agentes/modelo.py`](agentes/modelo.py).

Se quiser desligar a chave depois da aula, é na mesma página do AI Studio:
apagar a chave corta o acesso na hora.

---

## Instalação

Primeiro as três ferramentas. Elas se instalam uma vez só na sua máquina, não
uma vez por projeto — se você já tiver alguma, pule.

```bash
# 1. uv: instala o Python e as bibliotecas do projeto
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. just: o executor de receitas explicado acima
uv tool install rust-just

# 3. jq: formata o JSON que a API devolve, para dar para ler
sudo apt install jq
```

Não é engano: o pacote se chama `rust-just`, mas o comando que ele instala se
chama `just`. Feche e reabra o terminal, e confira as três de uma vez:

```bash
uv --version && just --version && jq --version
```

O `just` precisa ser 1.31 ou mais novo. Evite instalar por `apt`: em várias
distribuições a versão de lá é velha demais para os módulos que este projeto
usa.

Agora sim, **dentro da pasta do projeto**:

```bash
just sync                 # monta a .venv com o ADK 2.8.0 (uma vez)
cp .env.exemplo .env      # cole a chave de https://aistudio.google.com/apikey
just chave                # copia a chave para as quatro variantes
```

A variante 5 tem ambiente próprio e se instala à parte — veja
[`adk-basico/README.md`](adk-basico/README.md).

## Rodar

```bash
just web                  # interface no navegador, as quatro numa lista
just cli debate           # ou pelo terminal, uma de cada vez
```

Antes de gastar chamada:

```bash
just verificar            # as quatro carregam? (não fala com o modelo)
just testar-api           # a BrasilAPI responde? (não fala com o modelo)
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

Doze chamadas por pergunta: 3 debatedores × 3 rodadas + 1 mediador. Isso é
**doze vezes** o custo e a latência da variante 1, e nada na tela avisa.

E não é só custo. Medido no mesmo dia, seis chamadas seguidas a
`gemini-3.1-flash-lite` na cota gratuita deram **3 sucessos e 3 erros 503**. Com
50% de falha por chamada, a chance de as doze passarem é 0,5¹² — uma em quatro
mil. **O debate falhou três vezes seguidas** antes de existir o
[`agentes/modelo.py`](agentes/modelo.py), que liga repetição automática em
429/500/502/503/504 com espera que dobra a cada tentativa.

A conta vale além do Gemini: **num sistema de N passos em série, a
confiabilidade de cada passo entra elevada a N.** Encadear agentes multiplica a
fragilidade tão rápido quanto multiplica o custo. Repetição compra resiliência
contra falha transitória — não contra indisponibilidade.

## O que dá para mexer em aula

- **`conversa`** — mude a instrução e veja o comportamento mudar sem tocar em código.
- **`ferramenta`** — apague a linha `data:` do bloco `Args` da docstring e veja o
  agente começar a errar o formato. A docstring **é** a especificação.
  Peça também *"anote isso no seu arquivo"* e depois *"apague tudo"*: é a
  única ferramenta das nove que **muda** alguma coisa na sua máquina, e nada
  na tela pede confirmação.
- **`externa`** — desligue o wi-fi e veja a ferramenta devolver `{"erro": ...}`
  em vez de derrubar o turno.
- **`debate`** — mude `max_iterations` de 3 para 1 e compare custo e qualidade.
  Ou acrescente um quarto debatedor e veja quantas chamadas isso vira.

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
| `401`, `PERMISSION_DENIED`, `API key not valid` | chave errada, com espaço sobrando, ou não copiada para a pasta da variante — rode `just chave` |
| `429 RESOURCE_EXHAUSTED` | você bateu na cota gratuita. Espere um minuto |
| `503 ... high demand` | o servidor recusou. O `modelo.py` já repete sozinho; se insistir, espere |
| `adk: command not found` | você rodou fora do `uv run`. Use as receitas do `just` |
| A interface web não abre | ela sobe em <http://localhost:8000>, e o terminal fica ocupado enquanto ela está de pé |
