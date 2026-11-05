"""Fuentes externas permitidas (respaldo cuando una palabra no está en el catálogo).

Solo se consultan las URLs listadas en ALLOWED_SOURCES. La página se descarga una
vez, se convierte en una lista de pares (maya, español) y se guarda en memoria
(24 h). La búsqueda la hace Python: no gasta tokens ni da acceso libre a internet.

Formato soportado: tablas HTML de dos columnas <td>maya</td><td>español</td>
(como https://pueblosoriginarios.com/lenguas/mayas.php).
"""
from __future__ import annotations

import html
import logging
import re
import time
from urllib.parse import urlparse

import httpx

from .catalog import loose, normalize

log = logging.getLogger("traductor_maya")
_ROW = re.compile(r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")
_PAREN = re.compile(r"\([^)]*\)")
CACHE_SECONDS = 24 * 3600


def _clean(cell: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub("", cell))).replace("\xa0", " ").strip()


class ExternalSource:
    def __init__(self, url: str):
        self.url = url
        self.site = urlparse(url).hostname or url
        self.pairs: list[tuple[str, str]] = []  # (maya, español)
        self._loaded_at = 0.0

    def load_from_html(self, page: str) -> None:
        self.pairs = [(_clean(m), _clean(e)) for m, e in _ROW.findall(page) if _clean(m) and _clean(e)]
        self._loaded_at = time.time()

    async def ensure_loaded(self) -> bool:
        if self.pairs and time.time() - self._loaded_at < CACHE_SECONDS:
            return True
        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
                r = await client.get(self.url)
                r.raise_for_status()
            self.load_from_html(r.text)
            log.info("Fuente externa %s: %d entradas", self.site, len(self.pairs))
        except Exception:  # noqa: BLE001
            log.exception("No se pudo leer la fuente externa %s", self.url)
        return bool(self.pairs)

    def search(self, word: str, source: str = "auto", limit: int = 3) -> list[dict]:
        key, lkey = normalize(word), loose(word)
        exact, partial = [], []
        for maya, es in self.pairs:
            maya_variants = [loose(_PAREN.sub("", v)) for v in maya.split(",")]
            es_clean = normalize(_PAREN.sub("", es))
            es_variants = [normalize(v) for v in re.split(r"[,;/]", es_clean)]
            if source in ("maya", "auto") and lkey in maya_variants:
                exact.append((maya, es))
            elif source in ("es", "auto"):
                if key in es_variants:
                    exact.append((maya, es))
                elif re.search(rf"(^|\W){re.escape(key)}(\W|$)", es_clean):
                    partial.append((maya, es))
        hits = (exact + partial)[:limit]
        return [{"maya": m, "es": e, "fuente": self.site} for m, e in hits]


class ExternalSources:
    def __init__(self, urls: list[str]):
        self.sources = [ExternalSource(u) for u in urls if u.startswith("https://")]

    def __bool__(self) -> bool:
        return bool(self.sources)

    async def search(self, word: str, source: str = "auto") -> list[dict]:
        for s in self.sources:
            if await s.ensure_loaded():
                hits = s.search(word, source)
                if hits:
                    return hits
        return []
