"""Agente ASISTENTE: conversa con el usuario y pide traducciones al traductor por A2A."""
from __future__ import annotations

from typing import Annotated, Literal

import httpx
from a2a.client import A2ACardResolver
from agent_framework import tool
from agent_framework.a2a import A2AAgent

from .config import settings
from .llm import build_chat_client, default_options
from .tracking import TrackedAgent, current_session
from .translator_agent import A2A_KEY_HEADER
from .usage_store import UsageStore

ASSISTANT_INSTRUCTIONS = """Eres el ASISTENTE de un traductor de palabras sueltas entre español, inglés y maya yucateco.
- Responde en el idioma del usuario ({lang_hint}), breve y amable.
- Si piden traducir palabras, usa SIEMPRE la herramienta `traducir` (una sola llamada con todas las palabras).
- Nunca traduzcas por tu cuenta ni corrijas el resultado: muestra exactamente lo que devuelve `traducir`.
- Si el resultado dice NO_DISPONIBLE, explica que esa palabra aún no está en el catálogo.
- Solo traducimos palabras sueltas, no frases: si piden una frase, ofrece traducir sus palabras clave.
- Si preguntan otra cosa, di en una frase que solo ayudas con traducciones al maya y da un ejemplo de uso."""


class TranslatorConnection:
    """Cliente A2A del traductor. Descubre su tarjeta (Agent Card) en el primer uso."""

    def __init__(self) -> None:
        self._agent: A2AAgent | None = None
        self._http: httpx.AsyncClient | None = None

    async def get(self) -> A2AAgent:
        if self._agent is None:
            headers = {A2A_KEY_HEADER: settings.a2a_internal_key} if settings.a2a_internal_key else {}
            self._http = httpx.AsyncClient(headers=headers, timeout=60)
            card = await A2ACardResolver(self._http, settings.translator_url).get_agent_card()
            self._agent = A2AAgent(agent_card=card, http_client=self._http, forwarded_kwargs=["session_id"])
        return self._agent

    async def close(self) -> None:
        if self._http is not None:
            await self._http.aclose()


def build_assistant(usage: UsageStore, translator: TranslatorConnection, lang_hint: str = "español") -> TrackedAgent:
    @tool(name="traducir", description="Pide al agente traductor (vía A2A) traducir palabras sueltas.")
    async def traducir(
        palabras: Annotated[list[str], "Palabras sueltas a traducir"],
        idioma_origen: Annotated[Literal["es", "en", "maya", "auto"], "Idioma de las palabras"] = "auto",
        idioma_destino: Annotated[Literal["es", "en", "maya", "todos"], "Idioma al que se traduce"] = "maya",
    ) -> str:
        peticion = f"Traduce de {idioma_origen} a {idioma_destino}: " + ", ".join(palabras[:10])
        agent = await translator.get()
        respuesta = await agent.run(
            peticion, function_invocation_kwargs={"session_id": current_session.get() or ""}
        )
        return respuesta.text or "NO_DISPONIBLE"

    return TrackedAgent(
        build_chat_client(settings.assistant_model),
        ASSISTANT_INSTRUCTIONS.format(lang_hint=lang_hint),
        name="asistente",
        tools=[traducir],
        default_options=default_options(),
        usage_store=usage,
        usage_label="asistente",
    )
