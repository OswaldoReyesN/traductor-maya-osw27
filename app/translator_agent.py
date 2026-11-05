"""Agente TRADUCTOR, publicado como servidor A2A.

Solo traduce palabras que existen en el catálogo oficial (.md). La búsqueda la
hace Python (herramienta `buscar_en_catalogo`); el modelo solo interpreta la
petición y devuelve el resultado, sin inventar.
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
from .llm import build_chat_client, default_options
from .tracking import TrackedAgent
from .usage_store import UsageStore

A2A_KEY_HEADER = "X-A2A-Key"

TRANSLATOR_INSTRUCTIONS = """Eres el agente TRADUCTOR (español, inglés y maya yucateco).
Reglas estrictas:
1. Para CADA palabra pedida llama a `buscar_en_catalogo`. Nunca traduzcas de memoria.
2. Responde solo con lo que devuelva la herramienta, una línea por palabra:
   <palabra> (<idioma origen>) → <traducción(es) pedidas> [nota si existe]
   Si no se encontró: <palabra> → NO_DISPONIBLE
3. Sin saludos ni explicaciones extra. Sé breve."""


def build_translator(catalog: Catalog, usage: UsageStore) -> TrackedAgent:
    @tool(name="buscar_en_catalogo", description="Busca palabras en el catálogo oficial español/inglés/maya.")
    def buscar_en_catalogo(
        palabras: Annotated[list[str], "Palabras sueltas a buscar (máximo 10)"],
        idioma_origen: Annotated[Literal["es", "en", "maya", "auto"], "Idioma de las palabras, o 'auto'"] = "auto",
    ) -> str:
        found = [catalog.lookup(p, idioma_origen) for p in palabras[:10]]
        return json.dumps(found, ensure_ascii=False)

    tools = [buscar_en_catalogo]
    instructions = TRANSLATOR_INSTRUCTIONS
    if settings.allowed_sites:
        tools.append(_allowed_sites_tool())
        instructions += (
            "\n4. Solo si una palabra NO está en el catálogo puedes usar `consultar_sitio_permitido`, "
            "y debes indicar la fuente. Sitios permitidos: " + ", ".join(settings.allowed_sites)
        )

    return TrackedAgent(
        build_chat_client(settings.translator_model),
        instructions,
        name="traductor",
        description="Traduce palabras sueltas entre español, inglés y maya usando solo el catálogo oficial.",
        tools=tools,
        default_options=default_options(),
        usage_store=usage,
        usage_label="traductor",
    )


def _allowed_sites_tool():
    """Consulta web restringida a los dominios de ALLOWED_SITES (deshabilitada si está vacío)."""
    from urllib.parse import urlparse

    import httpx

    allowed = {d.lower().removeprefix("www.") for d in settings.allowed_sites}

    @tool(name="consultar_sitio_permitido", description="Lee una página de un sitio permitido en la configuración.")
    async def consultar_sitio_permitido(url: Annotated[str, "URL completa (https://...) de un sitio permitido"]) -> str:
        host = (urlparse(url).hostname or "").lower().removeprefix("www.")
        if urlparse(url).scheme != "https" or not any(host == d or host.endswith("." + d) for d in allowed):
            return "BLOQUEADO: el sitio no está en la lista de sitios permitidos."
        async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
            r = await client.get(url)
        return r.text[:2000]

    return consultar_sitio_permitido


def build_agent_card(url: str) -> AgentCard:
    return AgentCard(
        name="Traductor Maya",
        description="Traduce palabras sueltas español/inglés ↔ maya yucateco. Fuente única: catálogo oficial.",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        supported_interfaces=[AgentInterface(url=url, protocol_binding="JSONRPC", protocol_version="1.0")],
        skills=[
            AgentSkill(
                id="traducir_palabras",
                name="Traducir palabras",
                description="Traduce una o varias palabras sueltas usando el catálogo oficial.",
                tags=["traducción", "maya", "español", "inglés"],
                examples=["perro (es→maya)", "peek' (maya→es)", "water (en→maya)"],
            )
        ],
    )


class _RequireA2AKey(BaseHTTPMiddleware):
    """Protege el servidor A2A: solo el asistente (con la clave interna) puede usarlo."""

    async def dispatch(self, request, call_next):
        if settings.a2a_internal_key and request.headers.get(A2A_KEY_HEADER) != settings.a2a_internal_key:
            return JSONResponse({"error": "A2A no autorizado"}, status_code=401)
        return await call_next(request)


def build_a2a_app(catalog: Catalog, usage: UsageStore) -> Starlette:
    agent = build_translator(catalog, usage)
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
