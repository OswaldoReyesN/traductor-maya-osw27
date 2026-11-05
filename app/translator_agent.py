"""Agente TRADUCTOR, publicado como servidor A2A.

1. Busca en el catálogo oficial (.md) con Python.
2. Si no está y hay fuentes permitidas (ALLOWED_SOURCES), busca ahí, también con Python.
El modelo solo interpreta la petición y devuelve el resultado; nunca traduce de memoria.
"""
from __future__ import annotations

import json
from typing import Annotated, Literal

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from agent_framework import tool
from agent_framework.a2a import A2AExecutor
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .catalog import Catalog
from .config import settings
from .external_sources import ExternalSources
from .llm import build_chat_client, default_options
from .tracking import TrackedAgent
from .usage_store import UsageStore

A2A_KEY_HEADER = "X-A2A-Key"

TRANSLATOR_INSTRUCTIONS = """Eres el agente TRADUCTOR español ↔ maya yucateco.
Reglas estrictas:
1. Llama UNA vez a `buscar` con todas las palabras pedidas. Nunca traduzcas de memoria.
2. Devuelve solo los datos de la herramienta, una línea por palabra, con este formato:
   español: <es> | maya: <maya> | significado: <explicacion> | ejemplo: «<ejemplo_es>» = «<ejemplo_maya>» | fuente: <fuente>
   (usa los campos es y maya del resultado, no la palabra como la escribió el usuario)
   Omite los campos que no vengan. Copia el texto maya exactamente, letra por letra.
   Si la fuente no es el catálogo oficial, escribe "fuente: <sitio> (no está en el catálogo oficial)".
   Si no se encontró: <palabra> → NO_DISPONIBLE
3. Sin saludos ni explicaciones extra."""


def build_translator(catalog: Catalog, usage: UsageStore, external: ExternalSources) -> TrackedAgent:
    langs = tuple(settings.enabled_langs)

    @tool(name="buscar", description="Busca palabras en el catálogo oficial y, si faltan, en las fuentes permitidas.")
    async def buscar(
        palabras: Annotated[list[str], "Palabras sueltas a buscar (máximo 10)"],
        idioma_origen: Annotated[Literal["es", "maya", "auto"], "Idioma de las palabras, o 'auto'"] = "auto",
    ) -> str:
        results = []
        for p in palabras[:10]:
            r = catalog.lookup(p, idioma_origen)
            if not r["encontrada"] and external:
                hits = await external.search(p, idioma_origen)
                if hits:
                    r = {"palabra": p, "encontrada": True, "fuente": hits[0]["fuente"], "oficial": False, "resultados": hits}
            results.append(r)
        return json.dumps(results, ensure_ascii=False)

    return TrackedAgent(
        build_chat_client(settings.translator_model),
        TRANSLATOR_INSTRUCTIONS,
        name="traductor",
        description="Traduce palabras sueltas español ↔ maya usando el catálogo oficial y fuentes permitidas.",
        tools=[buscar],
        default_options=default_options(),
        usage_store=usage,
        usage_label="traductor",
    )


def build_agent_card(url: str) -> AgentCard:
    return AgentCard(
        name="Traductor Maya",
        description="Traduce palabras sueltas español ↔ maya yucateco. Fuente principal: catálogo oficial.",
        version="1.1.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        supported_interfaces=[AgentInterface(url=url, protocol_binding="JSONRPC", protocol_version="1.0")],
        skills=[
            AgentSkill(
                id="traducir_palabras",
                name="Traducir palabras",
                description="Traduce una o varias palabras sueltas, con significado y frase de ejemplo.",
                tags=["traducción", "maya", "español"],
                examples=["perro (es→maya)", "peek' (maya→es)"],
            )
        ],
    )


class _RequireA2AKey(BaseHTTPMiddleware):
    """Protege el servidor A2A: solo el asistente (con la clave interna) puede usarlo."""

    async def dispatch(self, request, call_next):
        if settings.a2a_internal_key and request.headers.get(A2A_KEY_HEADER) != settings.a2a_internal_key:
            return JSONResponse({"error": "A2A no autorizado"}, status_code=401)
        return await call_next(request)


def build_a2a_app(catalog: Catalog, usage: UsageStore, external: ExternalSources) -> Starlette:
    agent = build_translator(catalog, usage, external)
    card = build_agent_card(settings.translator_url)
    handler = DefaultRequestHandler(
        # Aceptamos solo "session_id" desde el asistente, para atribuir el consumo.
        agent_executor=A2AExecutor(agent, accepted_function_invocation_kwargs=["session_id"]),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    app = Starlette(routes=[*create_agent_card_routes(card), *create_jsonrpc_routes(handler, "/")])
    app.add_middleware(_RequireA2AKey)
    return app
