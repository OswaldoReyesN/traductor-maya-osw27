from pathlib import Path

from app.catalog import Catalog, normalize

CAT = Catalog.from_markdown(Path(__file__).parent.parent / "data" / "catalogo.md", ("es", "maya"))


def test_loads_all_tables():
    assert len(CAT) >= 150


def test_es_to_maya_with_example():
    r = CAT.lookup("Perro")
    e = r["resultados"][0]
    assert r["encontrada"] and e["maya"] == "peek'"
    assert e["ejemplo_es"] and e["ejemplo_maya"] and e["explicacion"]


def test_maya_without_apostrophe():
    r = CAT.lookup("peek")
    assert r["encontrada"] and r["resultados"][0]["es"] == "perro"


def test_maya_with_curly_apostrophe():
    r = CAT.lookup("ja’")
    assert r["encontrada"] and r["idioma_detectado"] == "maya" and r["resultados"][0]["es"] == "agua"


def test_spanish_synonym():
    assert CAT.lookup("tranquilidad")["resultados"][0]["maya"] == "jets' óolal"


def test_english_disabled():
    assert "en" not in CAT.lookup("perro")["resultados"][0]
    assert CAT.lookup("dog")["encontrada"] is False


def test_not_found_never_invents():
    r = CAT.lookup("computadora")
    assert r == {"palabra": "computadora", "encontrada": False, "resultados": []}


def test_normalize_keeps_enie():
    assert normalize("Niño") == "niño"
