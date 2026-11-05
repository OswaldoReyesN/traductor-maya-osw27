"""Aplicación web (FastAPI): página del chat, API del chat y servidor A2A del traductor."""
from __future__ import annotations

import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from agent_framework import Message
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .assistant_agent import TranslatorConnection, build_assistant
from .catalog import Catalog
from .config import settings
from .tracking import current_session
from .translator_agent import build_a2a_app
from .usage_store import UsageStore

log = logging.getLogger("traductor_maya")
STATIC = Path(__file__).parent / "static"

usage = UsageStore(settings.data_dir, settings.price_input_per_1m, settings.price_output_per_1m, settings.currency)
catalog = Catalog.from_markdown(settings.catalog_path)
translator = TranslatorConnection()
assistant = build_assistant(usage, translator)
history: dict[str, list[Message]] = {}  # solo en memoria, se pierde al reiniciar


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info("Catálogo cargado: %d palabras. Traductor A2A en %s", len(catalog), settings.translator_url)
    yield
    await translator.close()


app = FastAPI(title="Traductor Maya", lifespan=lifespan, docs_url=None, redoc_url=None)
app.mount("/a2a/translator", build_a2a_app(catalog, usage))
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class ChatIn(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    message: str = Field(min_length=1)


def _check_access(key: str | None) -> None:
    if settings.app_access_key and not secrets.compare_digest(key or "", settings.app_access_key):
        raise HTTPException(status_code=401, detail="Clave de acceso incorrecta.")


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


@app.get("/healthz")
async def healthz():
    return {"ok": True, "catalogo": len(catalog)}


@app.get("/api/config")
async def config():
    return {
        "requiere_clave": bool(settings.app_access_key),
        "max_caracteres": settings.max_input_chars,
        "palabras_en_catalogo": len(catalog),
        "modelo": settings.assistant_model,
    }


@app.get("/api/usage")
async def get_usage(session_id: str = "", x_access_key: str | None = Header(default=None)):
    _check_access(x_access_key)
    return usage.snapshot(session_id)


@app.post("/api/chat")
async def chat(body: ChatIn, x_access_key: str | None = Header(default=None)):
    _check_access(x_access_key)
    text = body.message.strip()
    sid = body.session_id
    # --- Límites para proteger los créditos --------------------------------
    if len(text) > settings.max_input_chars:
        raise HTTPException(400, f"Mensaje demasiado largo (máximo {settings.max_input_chars} caracteres).")
    if usage.day_tokens() >= settings.max_tokens_per_day:
        raise HTTPException(429, "Se alcanzó el límite diario de uso. Intenta mañana.")
    if usage.session_tokens(sid) >= settings.max_tokens_per_session:
        raise HTTPException(429, "Se alcanzó el límite de tokens de esta sesión. Recarga la página.")
    if usage.count_message(sid) > settings.max_messages_per_session:
        raise HTTPException(429, "Se alcanzó el límite de mensajes de esta sesión. Recarga la página.")

    # --- Historial corto: solo los últimos turnos (ahorro de tokens) ----------
    past = history.setdefault(sid, [])[-settings.history_turns * 2 :] if settings.history_turns > 0 else []
    token = current_session.set(sid)
    try:
        response = await assistant.run([*past, Message(role="user", contents=[text])])
    except Exception:  # noqa: BLE001
        log.exception("Error al llamar al modelo")
        raise HTTPException(502, "El servicio de IA no respondió. Intenta de nuevo en un momento.")
    finally:
        current_session.reset(token)
    reply = response.text or "…"
    history[sid] = [*past, Message(role="user", contents=[text]), Message(role="assistant", contents=[reply])]
    if len(history) > 500:  # evita crecer sin límite
        history.pop(next(iter(history)))
    return {"respuesta": reply, "consumo": usage.snapshot(sid)}
