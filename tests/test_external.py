from app.external_sources import ExternalSource

SAMPLE = """
<table><tr>  <td>peek’</td>  <td>sabueso (perro)&nbsp;</td> </tr>
<tr>  <td>aakbal</td>  <td>caparazón de tortuga&nbsp;</td> </tr>
<tr>  <td>kéeh (cervus communis)</td>  <td>venado </td> </tr></table>
"""


def _src():
    s = ExternalSource("https://ejemplo.org/diccionario")
    s.load_from_html(SAMPLE)
    return s


def test_parses_pairs():
    assert len(_src().pairs) == 3


def test_search_spanish_exact_and_partial():
    s = _src()
    assert s.search("venado")[0]["maya"].startswith("kéeh")
    assert s.search("caparazón")[0]["maya"] == "aakbal"


def test_search_maya_without_apostrophe():
    assert _src().search("peek", "maya")[0]["es"].startswith("sabueso")


def test_no_match():
    assert _src().search("computadora") == []
