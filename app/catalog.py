"""Catálogo oficial de palabras (archivo Markdown).

La búsqueda se hace con Python, sin gastar tokens del modelo. El modelo nunca
traduce por su cuenta: solo puede usar lo que devuelve esta búsqueda.

Formato esperado del archivo: una tabla Markdown con, al menos, las columnas
Español | English | Maya  (Categoría y Notas son opcionales).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

LANGS = ("es", "en", "maya")
_HEADER_ALIASES = {
    "es": {"español", "espanol", "spanish", "es"},
    "en": {"english", "inglés", "ingles", "en"},
    "maya": {"maya", "maaya", "maya yucateco", "myn", "yua"},
    "categoria": {"categoría", "categoria", "category"},
    "notas": {"notas", "notes", "nota"},
}
# Variantes del saltillo (glotal) que la gente escribe al teclear maya.
_APOSTROPHES = "’‘ʼ´`ꞌ"


@dataclass(frozen=True)
class Entry:
    es: str
    en: str
    maya: str
    categoria: str = ""
    notas: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def normalize(text: str) -> str:
    """Minúsculas, sin acentos, saltillo unificado y sin signos alrededor."""
    text = (text or "").strip().lower()
    for ch in _APOSTROPHES:
        text = text.replace(ch, "'")
    # Quitar acentos (pero conservar la ñ) para que "árbol" == "arbol".
    out = []
    for ch in unicodedata.normalize("NFD", text):
        if unicodedata.category(ch) == "Mn" and ch != "̃":
            continue
        out.append(ch)
    text = unicodedata.normalize("NFC", "".join(out))
    text = re.sub(r"^(el|la|los|las|un|una|the|a|an|to)\s+", "", text)
    return text.strip(" .,;:!¡?¿\"()[]")


def _variants(cell: str) -> list[str]:
    """Una celda puede tener sinónimos separados por '/' o ','."""
    return [normalize(p) for p in re.split(r"[/,]", cell) if normalize(p)]


class Catalog:
    def __init__(self, entries: list[Entry]):
        self.entries = entries
        self._index: dict[str, dict[str, list[Entry]]] = {lang: {} for lang in LANGS}
        for e in entries:
            for lang in LANGS:
                for v in _variants(getattr(e, lang)):
                    self._index[lang].setdefault(v, []).append(e)

    # ------------------------------------------------------------------
    @classmethod
    def from_markdown(cls, path: Path) -> "Catalog":
        text = Path(path).read_text(encoding="utf-8")
        entries: list[Entry] = []
        columns: dict[str, int] | None = None
        for raw in text.splitlines():
            line = raw.strip()
            if not line.startswith("|"):
                columns = None if not line else columns
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue  # separador |---|---|
            if columns is None:
                found = {}
                for i, c in enumerate(cells):
                    for key, aliases in _HEADER_ALIASES.items():
                        if c.lower().strip("* ") in aliases:
                            found[key] = i
                if all(k in found for k in LANGS):
                    columns = found
                continue
            get = lambda k: cells[columns[k]] if k in columns and columns[k] < len(cells) else ""  # noqa: E731
            if get("es") and get("maya"):
                entries.append(Entry(get("es"), get("en"), get("maya"), get("categoria"), get("notas")))
        return cls(entries)

    # ------------------------------------------------------------------
    def lookup(self, word: str, source: str = "auto") -> dict:
        """Busca una palabra. Devuelve un dict listo para el agente (JSON)."""
        key = normalize(word)
        langs = LANGS if source not in LANGS else (source,)
        for lang in langs:
            hits = self._index[lang].get(key)
            if hits:
                return {
                    "palabra": word,
                    "encontrada": True,
                    "idioma_detectado": lang,
                    "resultados": [h.to_dict() for h in hits],
                }
        return {"palabra": word, "encontrada": False, "resultados": []}

    def __len__(self) -> int:
        return len(self.entries)
