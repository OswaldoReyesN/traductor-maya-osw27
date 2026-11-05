"""Fábrica del cliente del modelo.

Aísla al resto de la app del proveedor: cambiar de cuenta, de modelo o de forma
de autenticación solo cambia variables de entorno.
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

from agent_framework import BaseChatClient, ChatResponse, Content, FunctionInvocationLayer, Message

from .config import settings


def default_options() -> dict[str, Any]:
    """Opciones de ahorro aplicadas a todas las llamadas."""
    opts: dict[str, Any] = {"max_tokens": settings.max_output_tokens}
    if settings.reasoning_effort and settings.llm_provider != "fake":
        opts["reasoning"] = {"effort": settings.reasoning_effort}
    return opts


def build_chat_client(model: str):
    provider = settings.llm_provider
    if provider == "fake":
        return FakeChatClient()
    if provider == "key":
        from agent_framework.openai import OpenAIChatClient

        return OpenAIChatClient(
            model,
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
        )
    # Por defecto: Microsoft Foundry con identidad de Entra.
    # Local: `az login`. En Azure App Service: identidad administrada (sin claves).
    from agent_framework.foundry import FoundryChatClient
    from azure.identity.aio import DefaultAzureCredential

    return FoundryChatClient(
        project_endpoint=settings.foundry_project_endpoint,
        model=model,
        credential=DefaultAzureCredential(exclude_interactive_browser_credential=True),
    )


# ---------------------------------------------------------------------------
# Modelo simulado: permite probar toda la app (incluido A2A) sin costo.
# Llama a la primera herramienta disponible con la última palabra del mensaje
# y luego responde con el resultado de la herramienta.
# ---------------------------------------------------------------------------
class _RawFake(BaseChatClient):
    OTEL_PROVIDER_NAME = "fake"

    async def _fake(self, messages, options) -> ChatResponse:
        tools = options.get("tools") or []
        last = messages[-1]
        results = [c for c in last.contents if c.type == "function_result"]
        usage = {"input_token_count": 50, "output_token_count": 10, "total_token_count": 60}
        if results:
            text = "; ".join(str(r.result) for r in results)
            return ChatResponse(messages=[Message(role="assistant", contents=[f"[fake] {text}"])], usage_details=usage)
        user_text = " ".join(c.text or "" for c in last.contents if c.type == "text")
        if tools:
            tool = tools[0]
            name = getattr(tool, "name", "tool")
            words = re.findall(r"[\w']+", user_text, re.UNICODE)
            word = words[-1] if words else user_text
            params = (getattr(tool, "parameters", lambda: {})() or {}).get("properties", {})
            args = {"palabras": [word]} if "palabras" in params else {k: word for k in params if k == "palabra"}
            call = Content.from_function_call(call_id=str(uuid.uuid4()), name=name, arguments=json.dumps(args))
            return ChatResponse(messages=[Message(role="assistant", contents=[call])], usage_details=usage)
        return ChatResponse(messages=[Message(role="assistant", contents=[f"[fake] {user_text}"])], usage_details=usage)

    def _inner_get_response(self, *, messages, stream, options, **kwargs):
        if stream:
            raise NotImplementedError("El modelo simulado no soporta streaming")
        return self._fake(messages, options)


class FakeChatClient(FunctionInvocationLayer, _RawFake):
    pass
