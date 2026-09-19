"""Cronômetro: os mesmos três pareceristas, em fila e em paralelo.

Não acredite que `ParallelAgent` é mais rápido: meça. Este script monta o
mesmo trio de `agent.py` duas vezes — uma dentro de um `SequentialAgent`,
outra dentro de um `ParallelAgent` — dá a eles o MESMO pedido de LAI e
cronometra. Três chamadas ao modelo de cada lado, seis no total.

    just cronometro                       # Gemini na nuvem (padrão)
    ADK_BACKEND=qwen3 just cronometro     # Qwen3 local
    just cronometro --protocolo 50001121584202581

O porteiro e o relator ficam de fora de propósito: eles são iguais nos dois
lados e só somariam tempo constante à medição. O pedido entra direto no
estado da sessão, por `state_delta`, que é o mesmo lugar onde o porteiro o
escreveria com `output_key="pedido"`.

O QUE ESPERAR
-------------
Gemini: o paralelo custa mais ou menos o tempo do parecer mais lento, e o
sequencial custa a soma dos três. Ganho perto de 3×.

Qwen3 local: empate. `servico-qwen/` é um processo só gerando token a token
na CPU; as três chamadas chegam juntas e entram numa fila mesmo assim. O
`ParallelAgent` fez a parte dele, o servidor é que não tem como.

A lição é essa: `ParallelAgent` paraleliza a ESPERA, não a CONTA.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

# `from modelo import modelo` só funciona com agentes/ no path. O `adk web`
# faz isso sozinho; rodando como script, a gente faz na mão.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.adk.agents import ParallelAgent, SequentialAgent  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

from paralelo.agent import criar_pareceristas  # noqa: E402
from paralelo.pedidos import buscar_pedido, carregar  # noqa: E402

APP = "cronometro"


def formatar(pedido: dict) -> str:
    """O mesmo formato que o porteiro produz em agent.py."""
    return (
        f"PROTOCOLO: {pedido['protocolo']}\n"
        f"ÓRGÃO: {pedido['orgao']}\n"
        f"DATA: {pedido['data_registro']}\n"
        f"ASSUNTO: {pedido['assunto']}\n"
        f"DECISÃO: {pedido['decisao']} ({pedido['especificacao_decisao'] or '—'})\n"
        f"MOTIVO DA NEGATIVA: {pedido['motivo_negativa'] or 'não se aplica'}\n\n"
        f"--- O QUE FOI PEDIDO ---\n{pedido['pedido']}\n\n"
        f"--- O QUE O ÓRGÃO RESPONDEU ---\n{pedido['resposta']}"
    )


async def cronometrar(rotulo: str, agente, texto: str) -> float:
    """Roda o agente uma vez e devolve o tempo de parede, em segundos."""
    runner = InMemoryRunner(agent=agente, app_name=APP)
    sessao = await runner.session_service.create_session(app_name=APP, user_id="aula")
    mensagem = types.Content(
        role="user", parts=[types.Part(text="Dê o seu parecer sobre este pedido.")]
    )

    print(f"  {rotulo:<15} rodando…", end="", flush=True)
    inicio = time.perf_counter()
    async for evento in runner.run_async(
        user_id="aula",
        session_id=sessao.id,
        new_message=mensagem,
        state_delta={"pedido": texto},   # onde o porteiro escreveria
    ):
        if evento.author and evento.is_final_response():
            print(f" {evento.author}", end="", flush=True)
    decorrido = time.perf_counter() - inicio
    print(f"  →  {decorrido:6.1f}s")
    return decorrido


async def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--protocolo", default="", help="padrão: o primeiro da amostra")
    args = p.parse_args()

    pedido = buscar_pedido(args.protocolo) if args.protocolo else dict(carregar()[0])
    if "erro" in pedido:
        raise SystemExit(f"ERRO: {pedido['erro']}")
    texto = formatar(pedido)

    backend = os.environ.get("ADK_BACKEND", "gemini")
    print(f"\nBackend: {backend}   ·   pedido {pedido['protocolo']} "
          f"({pedido['decisao']}, {len(texto)} caracteres)\n")

    fila = SequentialAgent(name="em_fila", sub_agents=criar_pareceristas())
    junto = ParallelAgent(name="em_paralelo", sub_agents=criar_pareceristas())

    t_fila = await cronometrar("SequentialAgent", fila, texto)
    t_junto = await cronometrar("ParallelAgent", junto, texto)

    print()
    razao = t_fila / max(t_junto, 1e-9)
    print(f"  Paralelo foi {razao:.1f}× o sequencial "
          f"({t_fila:.1f}s → {t_junto:.1f}s).")
    if razao < 1.3:
        print("  Empate. O gargalo não é a espera: é o servidor do modelo,")
        print("  que atende uma requisição de cada vez. Com o Qwen3 local")
        print("  isso é esperado — servico-qwen/ gera na CPU, um pedido por")
        print("  vez. Compare com a nuvem:  just cronometro")
    print()


if __name__ == "__main__":
    asyncio.run(main())
