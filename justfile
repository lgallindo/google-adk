# =============================================================================
# Agentes do 02173 — cinco variantes, uma rampa
#
# Padrão: Gemini na nuvem (precisa de chave do AI Studio).
#
#     just sync              .venv do ADK (uma vez)
#     just chave             copia a GOOGLE_API_KEY do .env para as variantes
#     just web               ADK em http://localhost:8000
#
# Qwen3 local (opcional, sem chave): just sync-qwen, just qwen-serve
# no terminal 1 e just web-qwen no terminal 2.
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

# ADK com Gemini (padrão). Precisa de just chave.
web:
    @echo "Backend: Gemini. Abra http://localhost:8000"
    uv run --no-active adk web agentes

web-memoria:
    @echo "Backend: Gemini + SQLite. Abra http://localhost:8000"
    uv run --no-active adk web agentes --session_service_uri sqlite:///sessoes.db

cli variante:
    uv run --no-active adk run agentes/{{variante}}

# --- Qwen3 local (opcional) --------------------------------------------------

web-qwen: _qwen-vivo
    @echo "Backend: Qwen3 local. Abra http://localhost:8000"
    ADK_BACKEND=qwen3 QWEN_API_BASE="{{QWEN_API_BASE}}" uv run --no-active adk web agentes

cli-qwen variante: _qwen-vivo
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
    # Toda pasta de agentes/ que tenha agent.py. Assim uma variante nova
    # nunca fica sem chave por esquecimento de editar esta lista.
    for d in agentes/*/; do
        [ -f "$d/agent.py" ] || continue
        cp .env "$d/.env"
        echo "  chave → $d"
    done

# Alias explícito, para quando o .env do aluno tiver ADK_BACKEND=qwen3.

web-gemini:
    @echo "Backend: Gemini. Abra http://localhost:8000"
    ADK_BACKEND=gemini uv run --no-active adk web agentes

cli-gemini variante:
    ADK_BACKEND=gemini uv run --no-active adk run agentes/{{variante}}

# Amostra de pedidos da LAI usada pela variante paralelo.
dados *args:
    uv run --no-active python agentes/paralelo/dados/baixar.py {{args}}

# O que tem na amostra da LAI (totais por decisão e por órgão).
amostra:
    uv run --no-active python agentes/paralelo/pedidos.py

# Lista os 60 pedidos com o gabarito. Cola de professor — não projete.
listar *decisao:
    uv run --no-active python agentes/paralelo/pedidos.py listar {{decisao}}

# Mostra um pedido inteiro, do jeito que o modelo o recebe.
ver protocolo:
    uv run --no-active python agentes/paralelo/pedidos.py ver {{protocolo}}

# O gabarito de um pedido da amostra: houve recurso de verdade?
gabarito protocolo:
    uv run --no-active python agentes/paralelo/pedidos.py {{protocolo}}

verificar *args:
    uv run --no-active python verificar.py {{args}}

testar-api:
    uv run --no-active python verificar.py --api
