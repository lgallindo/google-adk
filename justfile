# =============================================================================
# Agentes do 02173 — cinco variantes, uma rampa
#
# Padrão: Qwen3 local em servico-qwen/ (sem chave Google).
#
#     just sync              .venv do ADK (uma vez)
#     just sync-qwen         .venv do serviço Qwen (uma vez)
#     just qwen-serve        terminal 1 — modelo na porta 3000
#     just web               terminal 2 — ADK em http://localhost:8000
#
# Gemini (opcional): ADK_BACKEND=gemini + just chave + just web-gemini
# =============================================================================

PORT := env_var_or_default("PORT", "3000")
QWEN_API_BASE := env_var_or_default("QWEN_API_BASE", "http://127.0.0.1:" + PORT + "/v1")

default:
    @just --list

sync:
    uv sync --no-active

sync-qwen:
    cd servico-qwen && uv sync --no-active --extra-index-url https://download.pytorch.org/whl/cpu

# Terminal 1 — sobe o Qwen. Deixe aberto.
qwen-serve:
    #!/usr/bin/env bash
    set -euo pipefail
    if ss -ltn "sport = :{{PORT}}" | grep -q LISTEN; then
        echo "ERRO: porta {{PORT}} ocupada. Liberte-a ou: PORT=3001 just qwen-serve"
        echo "       (e no outro terminal: QWEN_API_BASE=http://127.0.0.1:3001/v1 just web)"
        exit 1
    fi
    echo "Qwen3 em http://127.0.0.1:{{PORT}} — depois: just web"
    cd servico-qwen && PORT="{{PORT}}" uv run --no-active bentoml serve service:QwenService --port "{{PORT}}"

_qwen-vivo:
    #!/usr/bin/env bash
    set -euo pipefail
    if curl -sf -m 3 -o /dev/null "{{QWEN_API_BASE}}/models"; then exit 0; fi
    echo "ERRO: Qwen não responde em {{QWEN_API_BASE}}"
    echo "  Terminal 1: just qwen-serve"
    echo "  Terminal 2: just web"
    exit 1

# Terminal 2 — ADK (Qwen por padrão).
web: _qwen-vivo
    @echo "Backend: Qwen3 local. Abra http://localhost:8000"
    ADK_BACKEND=qwen3 QWEN_API_BASE="{{QWEN_API_BASE}}" uv run --no-active adk web agentes

web-memoria: _qwen-vivo
    @echo "Backend: Qwen3 local + SQLite. Abra http://localhost:8000"
    ADK_BACKEND=qwen3 QWEN_API_BASE="{{QWEN_API_BASE}}" uv run --no-active adk web agentes --session_service_uri sqlite:///sessoes.db

cli variante: _qwen-vivo
    ADK_BACKEND=qwen3 QWEN_API_BASE="{{QWEN_API_BASE}}" uv run --no-active adk run agentes/{{variante}}

verificar-qwen: _qwen-vivo
    #!/usr/bin/env bash
    set -euo pipefail
    curl -sS -m 10 "{{QWEN_API_BASE}}/models" | jq .
    curl -sS -m 180 -X POST "{{QWEN_API_BASE}}/chat/completions" \
        -H 'Content-Type: application/json' \
        -d '{"model":"Qwen/Qwen3-0.6B","messages":[{"role":"user","content":"Say hi in one short sentence."}],"max_tokens":32,"temperature":0}' \
        | jq .

# --- Gemini (opcional) -------------------------------------------------------

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
    for v in conversa ferramenta externa debate ata; do
        cp .env "agentes/$v/.env"
        echo "  chave → agentes/$v/"
    done

web-gemini:
    @echo "Backend: Gemini. Precisa de just chave."
    @echo "Abra http://localhost:8000"
    ADK_BACKEND=gemini uv run --no-active adk web agentes

cli-gemini variante:
    ADK_BACKEND=gemini uv run --no-active adk run agentes/{{variante}}

verificar *args:
    uv run --no-active python verificar.py {{args}}

testar-api:
    uv run --no-active python verificar.py --api
