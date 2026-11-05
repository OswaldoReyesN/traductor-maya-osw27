"""Catálogo oficial de palabras (archivo Markdown).

La búsqueda se hace con Python, sin gastar tokens del modelo. El modelo nunca
traduce por su cuenta: solo puede usar lo que devuelve esta búsqueda.

Formato: una o varias tablas Markdown con, al menos, las columnas Español | Maya.
Columnas opcionales reconocidas: Inglés, Explicación (español), Ejemplo (español),
Ejemplo (maya), Ejemplo (inglés), Categoría, Notas.
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
    "explicacion": {"explicación (español)", "explicacion (español)", "explicación", "explicacion", "significado"},
    "ejemplo_es": {"ejemplo (español)", "ejemplo (espanol)", "ejemplo"},
    "ejemplo_en": {"ejemplo (inglés)", "ejemplo (ingles)"},
    "ejemplo_maya": {"ejemplo (maya)"},
    "categoria": {"categoría", "categoria", "category"},
    "notas": {"notas", "notes", "nota"},
}
# Variantes del saltillo (glotal) que la gente escribe al teclear maya.
_APOSTROPHES = "’‘ʼ´`ꞌ"


@dataclass(frozen=True)
class Entry:
    es: str
    maya: str
    en: str = ""
    explicacion: str = ""
    ejemplo_es: str = ""
    ejemplo_maya: str = ""
    ejemplo_en: str = ""
    categoria: str = ""
    notas: str = ""

    def to_dict(self, langs: tuple[str, ...] = LANGS) -> dict:
        """Solo los campos útiles para los idiomas activos (menos tokens)."""
        d = {k: v for k, v in asdict(self).items() if v}
        if "en" not in langs:
            d.pop("en", None)
            d.pop("ejemplo_en", None)
        return d


def normalize(text: str) -> str:
    """Minúsculas, sin acentos, saltillo unificado y sin signos alrededor."""
    text = (text or "").strip().lower()
    for ch in _APOSTROPHES:
        text = text.replace(ch, "'")
    out = []
    for ch in unicodedata.normalize("NFD", text):
        if unicodedata.category(ch) == "Mn" and ch != "̃":  # conserva la ñ
            continue
        out.append(ch)
    text = unicodedata.normalize("NFC", "".join(out))
    text = re.sub(r"^(el|la|los|las|un|una|the|a|an|to)\s+", "", text)
    return re.sub(r"\s+", " ", text.strip(" .,;:!¡?¿\"«»()[]"))


def loose(text: str) -> str:
    """Clave tolerante: además ignora el saltillo (peek == peek')."""
    return normalize(text).replace("'", "")


def _variants(cell: str) -> list[str]:
    """Una celda puede tener sinónimos separados por '/' o ','."""
    return [normalize(p) for p in re.split(r"[/,]", cell) if normalize(p)]


class Catalog:
    def __init__(self, entries: list[Entry], langs: tuple[str, ...] = LANGS):
        self.entries = entries
        self.langs = langs
        self._index: dict[str, dict[str, list[Entry]]] = {lang: {} for lang in LANGS}
        self._loose: dict[str, dict[str, list[Entry]]] = {lang: {} for lang in LANGS}
        for e in entries:
            for lang in LANGS:
                for v in _variants(getattr(e, lang)):
                    self._index[lang].setdefault(v, []).append(e)
                    self._loose[lang].setdefault(v.replace("'", ""), []).append(e)

    # ------------------------------------------------------------------
    @classmethod
    def from_markdown(cls, path: Path, langs: tuple[str, ...] = LANGS) -> "Catalog":
        text = Path(path).read_text(encoding="utf-8")
        entries: list[Entry] = []
        columns: dict[str, int] | None = None
        for raw in text.splitlines():
            line = raw.strip()
            if not line.startswith("|"):
                if line:
                    columns = None  # fin de la tabla
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue  # separador |---|---|
            if columns is None:
                found: dict[str, int] = {}
                for i, c in enumerate(cells):
                    label = c.lower().strip("* ")
                    for key, aliases in _HEADER_ALIASES.items():
                        if label in aliases and key not in found:
                            found[key] = i
                if "es" in found and "maya" in found:
                    columns = found
                continue
            row = {k: (cells[i] if i < len(cells) else "") for k, i in columns.items()}
            if row.get("es") and row.get("maya"):
                entries.append(Entry(**row))
        return cls(entries, langs)

    # ------------------------------------------------------------------
    def lookup(self, word: str, source: str = "auto") -> dict:
        """Busca una palabra. Devuelve un dict listo para el agente (JSON)."""
        langs = self.langs if source not in self.langs else (source,)
        for index, key in ((self._index, normalize(word)), (self._loose, loose(word))):
            for lang in langs:
                hits = index[lang].get(key)
                if hits:
                    return {
                        "palabra": word,
                        "encontrada": True,
                        "fuente": "catalogo_oficial",
                        "idioma_detectado": lang,
                        "resultados": [h.to_dict(self.langs) for h in hits[:3]],
                    }
        return {"palabra": word, "encontrada": False, "resultados": []}

    def __len__(self) -> int:
        return len(self.entries)
