"""Qwen3 local — OpenAI-compatible HTTP for the ADK (LiteLLM).

    just qwen-serve          # terminal 1
    just web                 # terminal 2 (ADK_BACKEND=qwen3 por padrão)
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

MODEL_NAME = os.environ.get("MODELO", "Qwen/Qwen3-0.6B")

_openai = Starlette(routes=[])


@bentoml.service(resources={"cpu": "2"})
@bentoml.asgi_app(_openai, path="/")
class QwenService:
    def __init__(self) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, dtype=dtype)
        self.model.eval()
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        _openai.router.routes.clear()
        _openai.router.routes.extend(
            [
                Route("/v1/chat/completions", self._chat, methods=["POST"]),
                Route("/v1/models", self._models, methods=["GET"]),
            ]
        )

    def _generate(self, messages: list[dict[str, Any]], max_new_tokens: int, temperature: float) -> dict[str, Any]:
        max_new_tokens = max(1, min(int(max_new_tokens), 512))
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
        kwargs: dict[str, Any] = {"tokenize": False, "add_generation_prompt": True}
        try:
            text = self.tokenizer.apply_chat_template(norm, enable_thinking=False, **kwargs)
        except TypeError:
            text = self.tokenizer.apply_chat_template(norm, **kwargs)
        inputs = self.tokenizer(text, return_tensors="pt")
        do_sample = temperature > 0.0
        gen: dict[str, Any] = {
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "pad_token_id": self.tokenizer.pad_token_id,
        }
        if do_sample:
            gen["temperature"] = temperature
        with torch.inference_mode():
            out = self.model.generate(**inputs, **gen)
        prompt_len = inputs["input_ids"].shape[-1]
        completion_ids = out[0][prompt_len:]
        return {
            "text": self.tokenizer.decode(completion_ids, skip_special_tokens=True).strip(),
            "prompt_tokens": int(prompt_len),
            "completion_tokens": int(completion_ids.shape[-1]),
        }

    async def _models(self, _request: Request) -> JSONResponse:
        return JSONResponse(
            {"object": "list", "data": [{"id": MODEL_NAME, "object": "model", "owned_by": "local"}]}
        )

    async def _chat(self, request: Request) -> JSONResponse:
        body = await request.json()
        if body.get("stream"):
            return JSONResponse({"error": "stream não suportado"}, status_code=400)
        messages = body.get("messages") or []
        if not messages:
            return JSONResponse({"error": "messages obrigatório"}, status_code=400)
        max_tokens = body.get("max_tokens") or body.get("max_completion_tokens") or 256
        temperature = float(body.get("temperature") or 0.0)
        result = self._generate(messages, int(max_tokens), temperature)
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
                    "total_tokens": result["prompt_tokens"] + result["completion_tokens"],
                },
            }
        )
