# =============================================================================
# Agentes do 02173 — quatro variantes, uma rampa
#
# Todas as variantes moram em agentes/ e usam o MESMO ambiente Python (o .venv
# da raiz), então basta um `just sync` para as quatro.
#
#     agentes/conversa/     1. só conversa. Nenhuma ferramenta.
#     agentes/ferramenta/   2. ferramenta é uma função Python local.
#     agentes/externa/      3. a ferramenta chama a BrasilAPI.
#     agentes/debate/       4. três agentes debatem 3 rodadas + um mediador.
#
# A quinta está em adk-basico/, com ambiente próprio, porque precisa de dois
# terminais e de bibliotecas que as outras quatro não usam. Ela é
# autossuficiente — o modelo e o serviço estão dentro dela:
#
#     adk-basico/           5. a ferramenta é um modelo de AM servido em HTTP.
#
# Como rodar:
#
#     just sync             instala o ambiente (uma vez)
#     just chave            copia a sua chave para as quatro variantes
#     just web              abre a interface e mostra as quatro numa lista
#     just cli conversa     conversa por terminal, sem navegador
# =============================================================================

default:
    @just --list

# Instala/atualiza a .venv a partir do pyproject.toml + uv.lock.
sync:
    uv sync --no-active

# Copia a chave do AI Studio para as quatro variantes.
# Antes de rodar: cp .env.exemplo .env e cole a sua chave no .env.
chave:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -f .env ]; then
        echo "ERRO: não existe .env aqui."
        echo ""
        echo "  1. cp .env.exemplo .env"
        echo "  2. abra .env e cole a chave de https://aistudio.google.com/apikey"
        echo "  3. rode 'just chave' de novo"
        exit 1
    fi
    if grep -q "cole-sua-chave-aqui" .env; then
        echo "ERRO: o .env ainda tem o texto de exemplo no lugar da chave."
        exit 1
    fi
    for v in conversa ferramenta externa debate; do
        cp .env "agentes/$v/.env"
        echo "  chave copiada para agentes/$v/"
    done

# Abre a interface web do ADK. As quatro variantes aparecem numa lista.
web:
    @echo "Abra http://localhost:8000 e escolha a variante na lista."
    uv run --no-active adk web agentes

# Conversa com UMA variante pelo terminal. Ex.: just cli debate
cli variante:
    uv run --no-active adk run agentes/{{variante}}

# Confere que as quatro variantes carregam sem erro, sem gastar chamada.
verificar *args:
    uv run --no-active python verificar.py {{args}}

# O mesmo, e ainda testa a BrasilAPI de verdade (sem chamar o modelo).
testar-api:
    uv run --no-active python verificar.py --api
