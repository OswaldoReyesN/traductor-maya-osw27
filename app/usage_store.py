"""Registro de consumo de tokens sin base de datos.

- Totales históricos y por día: archivo JSON (DATA_DIR/usage.json).
- Consumo por sesión: en memoria (se pierde al cerrar la página, como se acordó).

El acceso a este módulo está aislado: migrar a una base de datos después solo
requiere reescribir esta clase.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AGENTS = ("asistente", "traductor")


def _empty() -> dict[str, Any]:
    return {a: {"input": 0, "output": 0, "calls": 0} for a in AGENTS}


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class UsageStore:
    def __init__(self, data_dir: Path, price_in: float, price_out: float, currency: str = "USD"):
        self.path = Path(data_dir) / "usage.json"
        self.price_in = price_in
        self.price_out = price_out
        self.currency = currency
        self._lock = threading.Lock()
        self._sessions: dict[str, dict[str, Any]] = {}
        self._data = self._load()

    # ------------------------------------------------------------------ io
    def _load(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            data.setdefault("total", _empty())
            data.setdefault("days", {})
            return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {"total": _empty(), "days": {}}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)  # escritura atómica

    # -------------------------------------------------------------- record
    def record(self, agent: str, usage: dict | None, session_id: str | None = None) -> None:
        if agent not in AGENTS:
            agent = "asistente"
        usage = usage or {}
        tin = int(usage.get("input_token_count") or 0)
        tout = int(usage.get("output_token_count") or 0)
        with self._lock:
            buckets = [self._data["total"], self._data["days"].setdefault(_today(), _empty())]
            if session_id:
                buckets.append(self._sessions.setdefault(session_id, {"tokens": _empty(), "messages": 0})["tokens"])
            for b in buckets:
                b.setdefault(agent, {"input": 0, "output": 0, "calls": 0})
                b[agent]["input"] += tin
                b[agent]["output"] += tout
                b[agent]["calls"] += 1
            self._save()

    def count_message(self, session_id: str) -> int:
        with self._lock:
            s = self._sessions.setdefault(session_id, {"tokens": _empty(), "messages": 0})
            s["messages"] += 1
            return s["messages"]

    # ---------------------------------------------------------------- read
    def _summary(self, bucket: dict[str, Any]) -> dict[str, Any]:
        tin = sum(v["input"] for v in bucket.values())
        tout = sum(v["output"] for v in bucket.values())
        cost = tin / 1_000_000 * self.price_in + tout / 1_000_000 * self.price_out
        return {
            "por_agente": bucket,
            "entrada": tin,
            "salida": tout,
            "total": tin + tout,
            "costo_estimado": round(cost, 6),
            "moneda": self.currency,
        }

    def session_tokens(self, session_id: str) -> int:
        s = self._sessions.get(session_id)
        return self._summary(s["tokens"])["total"] if s else 0

    def day_tokens(self) -> int:
        return self._summary(self._data["days"].get(_today(), _empty()))["total"]

    def snapshot(self, session_id: str | None) -> dict[str, Any]:
        with self._lock:
            sess = self._sessions.get(session_id or "", {"tokens": _empty(), "messages": 0})
            return {
                "sesion": {**self._summary(sess["tokens"]), "mensajes": sess["messages"]},
                "hoy": self._summary(self._data["days"].get(_today(), _empty())),
                "historico": self._summary(self._data["total"]),
                "precios_por_millon": {"entrada": self.price_in, "salida": self.price_out},
            }
