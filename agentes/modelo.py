"""O modelo que as variantes usam.

Padrão: **Qwen3 local** (`servico-qwen/`, OpenAI-compatible em
`http://127.0.0.1:3000/v1`). Suba com `just qwen-serve` antes de `just web`.

Opcional: `ADK_BACKEND=gemini` + `GOOGLE_API_KEY` para a nuvem.

    ADK_BACKEND=qwen3|gemini     padrão: qwen3
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
    return os.environ.get("ADK_BACKEND", "qwen3").strip().lower()


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
    """Qwen3 local por padrão; Gemini se `ADK_BACKEND=gemini`."""
    if _backend() in ("gemini", "google", "cloud"):
        return _modelo_gemini()
    return _modelo_qwen()
