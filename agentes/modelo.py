"""O modelo que as variantes usam.

Padrão: **Gemini** na nuvem. Precisa de `GOOGLE_API_KEY` no `.env`
(`cp .env.exemplo .env` e depois `just chave`).

Opcional: `ADK_BACKEND=qwen3` usa o Qwen3 local de `servico-qwen/`
(OpenAI-compatible em `http://127.0.0.1:3000/v1`, suba com `just qwen-serve`).

    ADK_BACKEND=gemini|qwen3     padrão: gemini
    QWEN_API_BASE=http://127.0.0.1:3000/v1
    QWEN_MODEL=openai/Qwen/Qwen3-0.6B
"""

from __future__ import annotations

import os
from typing import Any

from google.adk.models import Gemini
from google.genai import types

NOME_GEMINI = "gemini-3.1-flash-lite"
NOME_QWEN_LITELLM = os.environ.get("QWEN_MODEL", "openai/Qwen/Qwen3-0.6B")
QWEN_API_BASE = os.environ.get("QWEN_API_BASE", "http://127.0.0.1:3000/v1")


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


def _modelo_qwen() -> Any:
    try:
        from google.adk.models.lite_llm import LiteLlm
    except ImportError as e:
        raise ImportError(
            "Qwen local precisa do LiteLLM. Neste repo rode: just sync\n"
            "(Pacote: google-adk[extensions] / litellm.)\n"
            "Não use o .venv de outra pasta de aula — o ADK tem que subir "
            "com: cd google-adk && just web"
        ) from e

    return LiteLlm(
        model=NOME_QWEN_LITELLM,
        api_base=QWEN_API_BASE,
        api_key=os.environ.get("QWEN_API_KEY", "local"),
        drop_params=True,
    )


def modelo() -> Any:
    """Gemini por padrão; Qwen3 local se `ADK_BACKEND=qwen3`."""
    if _backend() in ("qwen3", "qwen", "local"):
        return _modelo_qwen()
    return _modelo_gemini()
