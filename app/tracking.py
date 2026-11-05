"""Agente con registro automático de tokens.

Cada agente guarda su propio consumo en el archivo de uso. El id de la sesión del
chat viaja por A2A dentro de los metadatos (function_invocation_kwargs), así el
consumo del traductor también se suma a la sesión correcta.
"""
from __future__ import annotations

import contextvars
from typing import Any

from agent_framework import Agent

from .usage_store import UsageStore

# Sesión del chat que está siendo atendida (se propaga dentro de la misma tarea asyncio).
current_session: contextvars.ContextVar[str | None] = contextvars.ContextVar("current_session", default=None)


class TrackedAgent(Agent):
    def __init__(self, *args: Any, usage_store: UsageStore, usage_label: str, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._usage_store = usage_store
        self._usage_label = usage_label

    def run(self, messages=None, *, stream: bool = False, **kwargs: Any):  # type: ignore[override]
        if stream:
            return super().run(messages, stream=True, **kwargs)
        parent_run = super().run

        async def _run_and_track():
            response = await parent_run(messages, stream=False, **kwargs)
            fik = kwargs.get("function_invocation_kwargs") or {}
            session_id = fik.get("session_id") or current_session.get()
            self._usage_store.record(self._usage_label, response.usage_details, session_id)
            return response

        return _run_and_track()
