"""Límite de peticiones por IP (en memoria, ventana deslizante).

Sencillo y sin dependencias: suficiente para una sola instancia de App Service.
Si la app crece a varias instancias, se puede mover a Azure Front Door / API Management.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, per_minute: int, per_hour: int):
        self.rules = [(60, per_minute), (3600, per_hour)]
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> int:
        """Devuelve 0 si se permite; si no, los segundos que debe esperar."""
        now = time.time()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > 3600:
                q.popleft()
            for window, limit in self.rules:
                if limit <= 0:
                    continue
                recent = [t for t in q if now - t <= window]
                if len(recent) >= limit:
                    return int(window - (now - recent[0])) + 1
            q.append(now)
            if len(self._hits) > 5000:  # limpieza básica
                for k in [k for k, v in self._hits.items() if not v][:1000]:
                    del self._hits[k]
            return 0


def client_ip(headers, fallback: str = "") -> str:
    """En App Service la IP real viene en X-Forwarded-For (ip:puerto)."""
    fwd = headers.get("x-forwarded-for", "")
    ip = fwd.split(",")[0].strip() if fwd else fallback
    if ip.count(":") == 1:  # ipv4:puerto
        ip = ip.split(":")[0]
    return ip or "desconocida"
