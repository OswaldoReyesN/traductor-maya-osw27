from pathlib import Path

from app.catalog import Catalog, normalize

CAT = Catalog.from_markdown(Path(__file__).parent.parent / "data" / "catalogo.md")


def test_loads_entries():
    assert len(CAT) >= 10


def test_es_to_maya():
    r = CAT.lookup("Perro")
    assert r["encontrada"] and r["resultados"][0]["maya"] == "peek'"


def test_accents_and_articles_ignored():
    assert CAT.lookup("el maiz")["resultados"][0]["maya"] == "ixi'im"


def test_maya_with_curly_apostrophe():
    r = CAT.lookup("ja’")
    assert r["encontrada"] and r["idioma_detectado"] == "maya" and r["resultados"][0]["es"] == "agua"


def test_english_synonym():
    assert CAT.lookup("maize", "en")["resultados"][0]["es"] == "maíz"


def test_not_found_never_invents():
    r = CAT.lookup("computadora")
    assert r == {"palabra": "computadora", "encontrada": False, "resultados": []}


def test_normalize_keeps_enie():
    assert normalize("Niño") == "niño"
