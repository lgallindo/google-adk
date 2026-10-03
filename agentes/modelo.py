"""O modelo que as variantes usam.

Padrão: **Gemini** na nuvem (`gemini-3.1-flash-lite`).
Precisa de `GOOGLE_API_KEY` no `.env` (`cp .env.exemplo .env` e `just chave`).

Opcional — backend local OpenAI-compatible em `servico-local/`:

    ADK_BACKEND=local
    LOCAL_API_BASE=http://127.0.0.1:3000/v1
    LOCAL_MODEL=openai/<id-do-modelo-no-serviço>

Suba o serviço com `just local-serve` e o ADK com `just web-local`.

Histórico: um modelo bem pequeno (ordem de 0,6B parâmetros) foi tentado aqui
para aulas offline. Em prática ele **não** seguia tool calling nem prompts
com várias ferramentas de forma estável — o agente “conversava” sem chamar
funções, ou inventava argumentos. O serviço local atual usa um instruct
maior (`Qwen2.5-1.5B-Instruct` por padrão) precisamente para tool calling
mínimo; o caminho da disciplina e da AV2 continua sendo **Gemini**.
"""

from __future__ import annotations

import os
from typing import Any

from google.adk.models import Gemini
from google.genai import types

NOME_GEMINI = "gemini-3.1-flash-lite"
# Prefixo openai/ = LiteLLM fala com API OpenAI-compatible (servico-local).
NOME_LOCAL_LITELLM = os.environ.get(
    "LOCAL_MODEL", "openai/Qwen/Qwen2.5-1.5B-Instruct"
)
LOCAL_API_BASE = os.environ.get("LOCAL_API_BASE", "http://127.0.0.1:3000/v1")


def _backend() -> str:
    return os.environ.get("ADK_BACKEND", "gemini").strip().lower()


def _modelo_gemini() -> Gemini:
    return Gemini(
        model=NOME_GEMINI,
        retry_options=types.HttpRetryOptions(
            attempts=6,
            initial_delay=1.0,
            max_delay=30.0,
            exp_base=2.0,
            jitter=0.3,
            http_status_codes=[429, 500, 502, 503, 504],
        ),
    )


def _modelo_local() -> Any:
    """LiteLLM → HTTP OpenAI-compatible do `servico-local`."""
    try:
        from google.adk.models.lite_llm import LiteLlm
    except ImportError as e:
        raise ImportError(
            "Backend local precisa do LiteLLM. Neste repo: just sync\n"
            "(Pacote: google-adk[extensions] / litellm.)\n"
            "Não use o .venv de outra pasta de aula — rode da raiz: just web"
        ) from e

    return LiteLlm(
        model=NOME_LOCAL_LITELLM,
        api_base=LOCAL_API_BASE,
        api_key=os.environ.get("LOCAL_API_KEY", "local"),
        drop_params=True,
    )


def modelo() -> Any:
    """Gemini por padrão; local se `ADK_BACKEND=local` (aliases: qwen3, qwen)."""
    if _backend() in ("local", "qwen3", "qwen"):
        return _modelo_local()
    return _modelo_gemini()
