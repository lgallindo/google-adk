"""Serviço local OpenAI-compatible (BentoML) para o ADK via LiteLLM.

POR QUE ESTE ARQUIVO EXISTE
---------------------------
O ADK na nuvem usa Gemini (`agentes/modelo.py`, padrão). Este serviço é o
caminho **opcional** offline: sobe um modelo instruct por HTTP em
`/v1/chat/completions`, e o LiteLLM do ADK aponta para cá.

QUAL MODELO LOCAL
-----------------
O padrão é `Qwen/Qwen2.5-1.5B-Instruct`: cabe em CPU com paciência, ganha
com GPU, e sustenta tool calling mínimo em demos curtas. Instructs bem
menores (ordem de 0,6B) conversavam sem emitir chamada de função de forma
estável — por isso o piso da pasta é 1.5B.

Troque o modelo com a variável de ambiente `MODELO` (id Hugging Face).
O id exposto em `/v1/models` e no JSON de completions deve bater com
`LOCAL_MODEL` no lado do ADK (sem o prefixo `openai/` do LiteLLM).

    just local-serve          # terminal 1
    just web-local            # terminal 2  (ADK_BACKEND=local)

COMO AS PEÇAS SE ENCAIXAM (leitura de cima para baixo)
------------------------------------------------------
1. BentoML instancia `LocalLLMService` uma vez ao subir o processo.
2. No `__init__` baixamos/carregamos tokenizer + pesos HF (é o que demora).
3. Penduramos duas rotas Starlette no ASGI app embutido (`/v1/models` e
   `/v1/chat/completions`) — o contrato mínimo que o LiteLLM espera.
4. Cada POST em `/v1/chat/completions` vira: normalizar mensagens →
   `apply_chat_template` → `model.generate` → JSON no formato OpenAI.

Papéis `tool` no chat template: alguns modelos HF não têm role `tool`.
Aqui viramos `tool` → `user` com um prefixo `[tool result]`, para o
tokenizer não quebrar. Isso é gambiarra consciente do caminho local;
no Gemini o ADK trata tool calling nativamente.
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any

import bentoml
import torch
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from transformers import AutoModelForCausalLM, AutoTokenizer

# Id Hugging Face. Tem que ser o MESMO string que `/v1/models` devolve e que
# o ADK manda em LOCAL_MODEL *sem* o prefixo LiteLLM `openai/`.
# Instruct com tool-calling utilizável em demos curtas (não use 0.6B aqui).
MODEL_NAME = os.environ.get("MODELO", "Qwen/Qwen2.5-1.5B-Instruct")

# App ASGI “vazio” criado no import. O BentoML monta este objeto em `/`
# (@asgi_app abaixo). As rotas NÃO podem ser registradas aqui no import:
# os handlers são métodos da instância do serviço, que só existe depois do
# `__init__`. Por isso as Route(...) são acrescentadas lá dentro.
_openai = Starlette(routes=[])


@bentoml.service(resources={"cpu": "2"})
@bentoml.asgi_app(_openai, path="/")
class LocalLLMService:
    """Um processo = um modelo em memória + duas rotas OpenAI-compatible."""

    def __init__(self) -> None:
        # --- 1) Tokenizer -------------------------------------------------
        # Baixa (ou lê do cache HF) o tokenizer do MODEL_NAME. Sem ele não
        # dá para transformar o histórico de chat numa sequência de tokens.
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

        # --- 2) Pesos -----------------------------------------------------
        # float16 na GPU (menos VRAM, gera mais rápido); float32 na CPU
        # (float16 em CPU costuma ser mais lento ou nem suportado bem).
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, dtype=dtype)
        # Só inferência: desliga dropout / training hooks.
        self.model.eval()

        # --- 3) pad_token -------------------------------------------------
        # Vários instruct do Qwen vêm sem pad_token. O `generate` exige um
        # id de padding; reusar o eos é o truque usual e inofensivo aqui
        # (geramos uma sequência por vez, não um batch alinhado).
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # --- 4) Rotas OpenAI ----------------------------------------------
        # Limpa o que o Starlette tiver (restarts / reimport) e registra as
        # duas rotas que o LiteLLM chama. `self._chat` / `self._models` são
        # bound methods — por isso só dá para fazer isto depois do __init__.
        _openai.router.routes.clear()
        _openai.router.routes.extend(
            [
                Route("/v1/chat/completions", self._chat, methods=["POST"]),
                Route("/v1/models", self._models, methods=["GET"]),
            ]
        )

    def _generate(
        self, messages: list[dict[str, Any]], max_new_tokens: int, temperature: float
    ) -> dict[str, Any]:
        """Mensagens OpenAI → texto do assistente + contagem de tokens.

        Isto é a parte “modelo de verdade”. Tudo em volta só empacota HTTP.
        """
        # Teto duro: evita um max_tokens absurdo do cliente travar a CPU.
        max_new_tokens = max(1, min(int(max_new_tokens), 512))

        # --- Normalizar o histórico ---------------------------------------
        # LiteLLM/ADK às vezes manda `content` como lista de blocos
        # (multimodal). Só usamos texto. Role `tool` vira `user` com
        # prefixo — ver docstring do módulo.
        norm: list[dict[str, Any]] = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                content = "\n".join(
                    b.get("text", "") if isinstance(b, dict) else str(b) for b in content
                )
            role = msg.get("role", "user")
            if role == "tool":
                role, content = "user", f"[tool result]\n{content}"
            norm.append({"role": role, "content": content or ""})

        # --- Chat template ------------------------------------------------
        # O tokenizer do Qwen sabe marcar system/user/assistant. Sem isto o
        # modelo vê um blob cru e se perde. `add_generation_prompt=True`
        # acrescenta o marcador de “agora fala o assistente”.
        # `enable_thinking=False`: alguns templates Qwen recentes aceitam;
        # os antigos estouram TypeError — daí o try/except.
        kwargs: dict[str, Any] = {"tokenize": False, "add_generation_prompt": True}
        try:
            text = self.tokenizer.apply_chat_template(
                norm, enable_thinking=False, **kwargs
            )
        except TypeError:
            text = self.tokenizer.apply_chat_template(norm, **kwargs)

        inputs = self.tokenizer(text, return_tensors="pt")

        # temperature 0 → guloso (determinístico o bastante para demo).
        do_sample = temperature > 0.0
        gen: dict[str, Any] = {
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "pad_token_id": self.tokenizer.pad_token_id,
        }
        if do_sample:
            gen["temperature"] = temperature

        # --- Gerar --------------------------------------------------------
        # `inference_mode` = sem autograd (menos RAM, mais rápido).
        # `out` traz prompt + continuação; cortamos o prompt para devolver
        # só o que o assistente acabou de escrever.
        with torch.inference_mode():
            out = self.model.generate(**inputs, **gen)
        prompt_len = inputs["input_ids"].shape[-1]
        completion_ids = out[0][prompt_len:]
        return {
            "text": self.tokenizer.decode(
                completion_ids, skip_special_tokens=True
            ).strip(),
            "prompt_tokens": int(prompt_len),
            "completion_tokens": int(completion_ids.shape[-1]),
        }

    async def _models(self, _request: Request) -> JSONResponse:
        """GET /v1/models — o LiteLLM confere que o id existe antes de chat."""
        return JSONResponse(
            {
                "object": "list",
                "data": [
                    {
                        "id": MODEL_NAME,
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "local",
                    }
                ],
            }
        )

    async def _chat(self, request: Request) -> JSONResponse:
        """POST /v1/chat/completions — corpo OpenAI in, JSON OpenAI out.

        Só os campos que o LiteLLM/ADK leem: choices[0].message.content e
        usage. Não implementamos stream, tools nativas do protocolo OpenAI,
        nem logprobs — o ADK local usa o texto da mensagem.
        """
        body = await request.json()
        messages = body.get("messages") or []
        max_new = body.get("max_tokens") or body.get("max_completion_tokens") or 128
        temperature = float(body.get("temperature", 0.0))
        result = self._generate(messages, int(max_new), temperature)
        return JSONResponse(
            {
                "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": body.get("model") or MODEL_NAME,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": result["text"]},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": result["prompt_tokens"],
                    "completion_tokens": result["completion_tokens"],
                    "total_tokens": result["prompt_tokens"]
                    + result["completion_tokens"],
                },
            }
        )
