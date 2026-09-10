"""Confere que as quatro variantes carregam, sem gastar chamada ao modelo.

Importar o módulo do agente já valida o que mais quebra na prática: nome de
classe errado, `output_key` em agente que não é LlmAgent, sub-agente faltando,
docstring de ferramenta mal formada. Nada aqui fala com a API do Gemini.

    just verificar          só carrega os quatro
    just verificar --api    carrega e ainda testa a BrasilAPI de verdade
"""

import importlib
import sys
from pathlib import Path

# O `adk` põe a pasta agentes/ no sys.path e carrega cada variante como módulo
# de primeiro nível — é por isso que os agent.py escrevem `from modelo import
# modelo`, e não `from ..modelo import ...`. Aqui fazemos igual, para que este
# script quebre exatamente quando o `adk` quebraria.
sys.path.insert(0, str(Path(__file__).parent / "agentes"))

VARIANTES = ("conversa", "ferramenta", "externa", "debate")


def carregar(nome: str) -> None:
    agente = importlib.import_module(f"{nome}.agent").root_agent
    subs = getattr(agente, "sub_agents", None) or []
    ferramentas = getattr(agente, "tools", None) or []

    detalhes = []
    if subs:
        detalhes.append(f"{len(subs)} sub-agentes: {', '.join(s.name for s in subs)}")
    if ferramentas:
        nomes = [getattr(f, "__name__", str(f)) for f in ferramentas]
        detalhes.append(f"{len(ferramentas)} ferramentas: {', '.join(nomes)}")

    sufixo = f" — {' · '.join(detalhes)}" if detalhes else ""
    print(f"  ok  {nome:12} {type(agente).__name__} {agente.name!r}{sufixo}")


def testar_api() -> None:
    from externa.agent import consultar_cep, feriados_do_ano, proximo_feriado

    print("\n  BrasilAPI (chamadas de verdade, sem modelo):")
    prox = proximo_feriado()
    print(f"    proximo_feriado -> {prox}")

    ano = feriados_do_ano(2026)
    print(f"    feriados_do_ano -> ano {ano.get('ano')}, {ano.get('quantidade')} feriados")

    cep = consultar_cep("50030-230")
    print(f"    consultar_cep   -> {cep.get('street', cep)}, {cep.get('city', '')}")


if __name__ == "__main__":
    print("Variantes:")
    for nome in VARIANTES:
        carregar(nome)

    if "--api" in sys.argv:
        testar_api()

    print("\nTudo carregou. Nenhuma chamada ao modelo foi feita.")
