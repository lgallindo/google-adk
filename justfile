# =============================================================================
# Agentes ADK — rampa numerada (00 → 09)
#
# Padrão: Gemini na nuvem (precisa de chave do AI Studio).
#
#     just sync              .venv do ADK (uma vez)
#     just chave             copia a GOOGLE_API_KEY do .env para as variantes
#     just web               ADK em http://localhost:8000
#     just cli 00_conversa   um agente no terminal
#
# Local opcional (servico-local): just sync-local, just local-serve,
# depois just web-local.
# =============================================================================

PORT := env_var_or_default("PORT", "3000")
LOCAL_API_BASE := env_var_or_default("LOCAL_API_BASE", "http://127.0.0.1:" + PORT + "/v1")

default:
    @just --list

sync:
    uv sync --no-active

sync-local:
    cd servico-local && uv sync --no-active --extra-index-url https://download.pytorch.org/whl/cpu

# Terminal 1 — modelo local OpenAI-compatible. Deixe aberto.
local-serve:
    #!/usr/bin/env bash
    set -euo pipefail
    if ss -ltn "sport = :{{PORT}}" | grep -q LISTEN; then
        echo "ERRO: porta {{PORT}} ocupada. Liberte-a ou: PORT=3001 just local-serve"
        echo "       (e no outro terminal: LOCAL_API_BASE=http://127.0.0.1:3001/v1 just web-local)"
        exit 1
    fi
    echo "Modelo local em http://127.0.0.1:{{PORT}} — depois: just web-local"
    cd servico-local && PORT="{{PORT}}" uv run --no-active bentoml serve service:LocalLLMService --port "{{PORT}}"

_local-vivo:
    #!/usr/bin/env bash
    set -euo pipefail
    if curl -sf -m 3 -o /dev/null "{{LOCAL_API_BASE}}/models"; then exit 0; fi
    echo "ERRO: serviço local não responde em {{LOCAL_API_BASE}}"
    echo "  Terminal 1: just local-serve"
    echo "  Terminal 2: just web-local"
    exit 1

# ADK com Gemini (padrão). Precisa de just chave.
web:
    @echo "Backend: Gemini. Abra http://localhost:8000"
    uv run --no-active adk web agentes

web-memoria:
    @echo "Backend: Gemini + SQLite. Abra http://localhost:8000"
    uv run --no-active adk web agentes --session_service_uri sqlite:///sessoes.db

cli variante:
    uv run --no-active adk run agentes/{{variante}}

# --- Backend local (opcional) ------------------------------------------------

web-local: _local-vivo
    @echo "Backend: local. Abra http://localhost:8000"
    ADK_BACKEND=local LOCAL_API_BASE="{{LOCAL_API_BASE}}" uv run --no-active adk web agentes

cli-local variante: _local-vivo
    ADK_BACKEND=local LOCAL_API_BASE="{{LOCAL_API_BASE}}" uv run --no-active adk run agentes/{{variante}}

verificar-local: _local-vivo
    #!/usr/bin/env bash
    set -euo pipefail
    curl -sS -m 10 "{{LOCAL_API_BASE}}/models" | jq .
    curl -sS -m 180 -X POST "{{LOCAL_API_BASE}}/chat/completions" \
        -H 'Content-Type: application/json' \
        -d '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[{"role":"user","content":"Say hi in one short sentence."}],"max_tokens":32,"temperature":0}' \
        | jq .

# Aliases explícitos Gemini (iguais a web/cli — o padrão já é Gemini).

web-gemini:
    @echo "Backend: Gemini. Abra http://localhost:8000"
    ADK_BACKEND=gemini uv run --no-active adk web agentes

cli-gemini variante:
    ADK_BACKEND=gemini uv run --no-active adk run agentes/{{variante}}

chave:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -f .env ]; then
        echo "ERRO: cp .env.exemplo .env e cole a chave do AI Studio"
        exit 1
    fi
    if grep -q "cole-sua-chave-aqui" .env; then
        echo "ERRO: ainda está cole-sua-chave-aqui no .env"
        exit 1
    fi
    for d in agentes/*/; do
        [ -f "$d/agent.py" ] || continue
        cp .env "$d/.env"
        echo "  chave → $d"
    done

# Amostra de pedidos (variante 08_paralelo).
dados *args:
    uv run --no-active python agentes/08_paralelo/dados/baixar.py {{args}}

amostra:
    uv run --no-active python agentes/08_paralelo/pedidos.py

listar *decisao:
    uv run --no-active python agentes/08_paralelo/pedidos.py listar {{decisao}}

ver protocolo:
    uv run --no-active python agentes/08_paralelo/pedidos.py ver {{protocolo}}

gabarito protocolo:
    uv run --no-active python agentes/08_paralelo/pedidos.py {{protocolo}}

verificar *args:
    uv run --no-active python verificar.py {{args}}

testar-api:
    uv run --no-active python verificar.py --api
