"""Variante 2 — ferramenta é uma função Python. Só isso.

A diferença para a variante `conversa` são as funções abaixo e a linha
`tools=[...]` no fim. Não existe registro de ferramentas, não existe arquivo de
configuração, não existe JSON Schema escrito à mão.

O QUE O ADK LÊ DE CADA FUNÇÃO
-----------------------------
Ele monta a descrição da ferramenta a partir de três coisas que você já escreve
em Python normal:

    def dias_ate(data: str) -> dict:
        ^^^^^^^^  ^^^^^^^^^^^    ^^^^
        o nome    os tipos       o tipo de retorno
        \"\"\"A primeira linha vira a descrição da ferramenta.

        Args:
            data: esta linha vira a descrição do parâmetro.
        \"\"\"

Medido nesta versão (ADK 2.8.0), o que chega ao modelo é isto:

    description = a docstring INTEIRA, bloco `Args:` incluído
    schema      = só os nomes e os tipos — sem nenhuma das explicações

Ou seja: as suas explicações chegam, mas pela porta da descrição, não pela do
schema. Mude a docstring e o comportamento do agente muda, **sem tocar no
modelo**. Esse é o exercício: apague a linha `data:` do bloco `Args` e veja o
agente começar a errar o formato da data.

O QUE ISSO CONSERTA
-------------------
Na variante `conversa` o agente inventava contas e não sabia que dia era hoje.
Aqui ele não precisa saber: quem conta é Python, que não erra aritmética, e
quem olha o relógio é o sistema operacional. O modelo só decide QUANDO chamar
e COM QUAIS argumentos.

DOIS TIPOS DE FERRAMENTA, E A LINHA ENTRE ELES
----------------------------------------------
As ferramentas aqui se dividem em duas famílias, e vale reparar na diferença:

    só respondem            dias_ate, sortear, data_de_hoje, hora_agora,
                            pasta_atual, listar_arquivos, nome_do_computador,
                            ler_arquivo
    MEXEM na sua máquina    escrever_arquivo

Chamar uma da primeira família duas vezes é igual a chamar uma vez. A segunda
**apaga o que estava lá**. Quem decide chamá-la é o modelo, em tempo de
execução — você não escreveu nenhum `if`. É a mesma capacidade que faz o Claude
Code e o Cursor funcionarem, e é exatamente por isso que eles pedem confirmação
antes de escrever. Aqui não pedem: repare no que isso significa.

Por segurança, `ler_arquivo` e `escrever_arquivo` **não recebem caminho**. Elas
trabalham num arquivo único e fixo, `arquivo_do_agente.md`, na pasta de onde
você rodou o `just`. Sem parâmetro de caminho, não existe caminho para o modelo
errar.
"""

import platform
import random
import socket
from datetime import date, datetime
from pathlib import Path

from google.adk.agents import Agent

from modelo import modelo

# O único arquivo que este agente pode ler e escrever. Caminho relativo de
# propósito: ele resolve para a pasta de onde você rodou o `just`, que é o que
# `pasta_atual()` devolve.
ARQUIVO = Path("arquivo_do_agente.md")


def dias_ate(data: str) -> dict:
    """Conta quantos dias faltam de hoje até uma data.

    Args:
        data: a data alvo no formato AAAA-MM-DD, por exemplo "2026-09-24".
    """
    try:
        alvo = date.fromisoformat(data)
    except ValueError:
        return {"erro": f"'{data}' não está no formato AAAA-MM-DD"}

    faltam = (alvo - date.today()).days
    return {"data": data, "hoje": date.today().isoformat(), "dias": faltam}


def sortear(opcoes: list[str], quantas: int = 1) -> dict:
    """Sorteia uma ou mais opções de uma lista, sem repetir.

    Args:
        opcoes: a lista de onde sortear, por exemplo ["Ana", "Bruno", "Caio"].
        quantas: quantas opções sortear. O padrão é 1.

    Returns:
        Um dicionário com a lista de sorteadas e a quantidade total de opções.
    """
    if not opcoes:
        return {"erro": "a lista está vazia"}
    quantas = max(1, min(quantas, len(opcoes)))
    return {"sorteadas": random.sample(opcoes, quantas), "de": len(opcoes)}


def data_de_hoje() -> dict:
    """Diz que dia é hoje, com o dia da semana. Não recebe nada."""
    hoje = date.today()
    semana = (
        "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
        "sexta-feira", "sábado", "domingo",
    )
    return {
        "data": hoje.isoformat(),
        "dia_da_semana": semana[hoje.weekday()],
        "dia": hoje.day,
        "mes": hoje.month,
        "ano": hoje.year,
    }


def hora_agora() -> dict:
    """Diz que horas são agora, no fuso do computador. Não recebe nada."""
    agora = datetime.now().astimezone()
    return {
        "hora": agora.strftime("%H:%M:%S"),
        "fuso": agora.strftime("%Z (UTC%z)"),
        "iso": agora.isoformat(timespec="seconds"),
    }


def pasta_atual() -> dict:
    """Diz em que pasta o agente está rodando. Não recebe nada."""
    aqui = Path.cwd()
    return {"pasta": str(aqui), "nome": aqui.name}


def listar_arquivos() -> dict:
    """Lista os arquivos e pastas da pasta atual. Não recebe nada."""
    itens = sorted(
        p for p in Path.cwd().iterdir() if not p.name.startswith(".")
    )
    mostrados = itens[:50]
    return {
        "arquivos": [p.name for p in mostrados if p.is_file()],
        "pastas": [p.name + "/" for p in mostrados if p.is_dir()],
        "total": len(itens),
        "omitidos": len(itens) - len(mostrados),
    }


def nome_do_computador() -> dict:
    """Diz o nome (hostname) e o sistema do computador. Não recebe nada."""
    return {
        "hostname": socket.gethostname(),
        "sistema": f"{platform.system()} {platform.release()}",
    }


def ler_arquivo() -> dict:
    """Lê o arquivo de anotações do agente, o arquivo_do_agente.md.

    Não recebe nada: o arquivo é sempre esse, na pasta atual.
    """
    if not ARQUIVO.exists():
        return {"existe": False, "conteudo": "", "dica": "ainda não foi criado"}
    conteudo = ARQUIVO.read_text(encoding="utf-8")
    return {
        "existe": True,
        "conteudo": conteudo,
        "caracteres": len(conteudo),
        "linhas": conteudo.count("\n") + 1,
    }


def escrever_arquivo(conteudo_novo: str) -> dict:
    """Substitui TODO o conteúdo do arquivo_do_agente.md pelo texto dado.

    Isto APAGA o que já estava no arquivo. Para não perder nada, chame
    `ler_arquivo` antes e mande de volta o texto antigo junto com o novo.

    Args:
        conteudo_novo: o texto completo que o arquivo deve passar a ter.
    """
    antes = len(ARQUIVO.read_text(encoding="utf-8")) if ARQUIVO.exists() else 0
    ARQUIVO.write_text(conteudo_novo, encoding="utf-8")
    return {
        "arquivo": str(ARQUIVO.resolve()),
        "caracteres_antes": antes,
        "caracteres_depois": len(conteudo_novo),
        "apagados": max(0, antes - len(conteudo_novo)),
    }


root_agent = Agent(
    name="ferramenta",
    model=modelo(),
    description=(
        "Consulta data, hora, pasta, arquivos e nome da máquina; conta dias, "
        "sorteia nomes e mantém um bloco de anotações em disco."
    ),
    instruction=(
        "Você ajuda a turma usando as ferramentas que tem. "
        "NUNCA responda de cabeça o que uma ferramenta sabe: data, hora, "
        "nome da máquina, pasta, lista de arquivos e conta de dias vêm "
        "SEMPRE da ferramenta, porque você não tem como saber nada disso. "
        "Use SEMPRE a ferramenta para sortear — se você 'escolher' sozinho, "
        "não é sorteio. "
        "Antes de chamar `escrever_arquivo`, chame SEMPRE `ler_arquivo` "
        "primeiro e inclua o conteúdo antigo no texto novo, a menos que a "
        "pessoa tenha pedido explicitamente para apagar tudo — "
        "`escrever_arquivo` substitui o arquivo inteiro. "
        "Depois de escrever, diga em uma frase o que mudou. "
        "Explique cada resultado em uma frase, sem repetir o JSON."
    ),
    tools=[
        dias_ate,
        sortear,
        data_de_hoje,
        hora_agora,
        pasta_atual,
        listar_arquivos,
        nome_do_computador,
        ler_arquivo,
        escrever_arquivo,
    ],
)
