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

ASSISTANT_INSTRUCTIONS = """Eres un asistente cálido y cercano que ayuda a aprender palabras en maya yucateco.
Hablas en español, con frases naturales y breves, como una persona amable que enseña (sin exagerar ni usar listas largas).

Cuándo traducir (llama a `traducir` UNA vez con todas las palabras):
- "¿cómo se dice X?", "traduce X", "X en maya", "¿qué significa X?", "¿qué es X?", o un mensaje con solo palabras.
- Si la palabra parece maya (lleva apóstrofo o no es español), usa idioma_origen="maya".

Cómo responder con el resultado:
- Di la traducción en negritas, por ejemplo: "*Perro* en maya se dice **peek'**."
- Añade el significado en pocas palabras y la frase de ejemplo si viene: «español» → «maya».
- Si la fuente no es el catálogo oficial, menciónalo con naturalidad (ej.: "No la tengo en mi catálogo, pero en pueblosoriginarios.com aparece como…").
- Si es NO_DISPONIBLE, dilo con amabilidad y sugiere probar con otra palabra parecida.
- Puedes cerrar, a veces, con una pregunta breve para seguir practicando.

Reglas estrictas:
- NUNCA escribas palabras o frases en maya que no vengan del resultado de `traducir` (ni saludos, ni ejemplos). Cópialas exactas.
- Solo traducimos palabras sueltas: si piden una frase, ofrece traducir sus palabras clave.
- Por ahora solo trabajamos español ↔ maya: si escriben en inglés, explica amablemente (en inglés y en español) que por el momento solo usamos español.
- Si el mensaje no es sobre traducir, responde con calidez en una o dos frases que tu especialidad es el maya y sugiere: "¿cómo se dice perro en maya?"."""


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


def build_assistant(usage: UsageStore, translator: TranslatorConnection) -> TrackedAgent:
    @tool(name="traducir", description="Pide al agente traductor (vía A2A) traducir palabras sueltas.")
    async def traducir(
        palabras: Annotated[list[str], "Palabras sueltas a traducir"],
        idioma_origen: Annotated[Literal["es", "maya", "auto"], "Idioma de las palabras"] = "auto",
        idioma_destino: Annotated[Literal["es", "maya"], "Idioma al que se traduce"] = "maya",
    ) -> str:
        peticion = f"Traduce de {idioma_origen} a {idioma_destino}: " + ", ".join(palabras[:10])
        agent = await translator.get()
        respuesta = await agent.run(
            peticion, function_invocation_kwargs={"session_id": current_session.get() or ""}
        )
        return respuesta.text or "NO_DISPONIBLE"

    return TrackedAgent(
        build_chat_client(settings.assistant_model),
        ASSISTANT_INSTRUCTIONS,
        name="asistente",
        tools=[traducir],
        default_options=default_options(),
        usage_store=usage,
        usage_label="asistente",
    )
