"""Prueba de punta a punta con el modelo simulado (sin costo, sin Azure)."""
import os
import socket
import threading
import time

import httpx
import pytest


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    port = _free_port()
    os.environ.update(
        LLM_PROVIDER="fake", PORT=str(port), A2A_INTERNAL_KEY="k-interna",
        APP_ACCESS_KEY="clave", DATA_DIR=str(tmp_path_factory.mktemp("data")), MAX_MESSAGES_PER_SESSION="5",
        RATE_LIMIT_PER_MINUTE="1000", ALLOWED_SOURCES="",
    )
    import uvicorn

    from app.main import app

    cfg = uvicorn.Config(app, port=port, log_level="warning")
    srv = uvicorn.Server(cfg)
    threading.Thread(target=srv.run, daemon=True).start()
    for _ in range(50):
        if srv.started:
            break
        time.sleep(0.1)
    yield f"http://127.0.0.1:{port}"
    srv.should_exit = True


def _chat(base, msg, sid="sesion-prueba-1", key="clave"):
    return httpx.post(f"{base}/api/chat", json={"session_id": sid, "message": msg}, headers={"X-Access-Key": key}, timeout=30)


def test_requires_access_key(server):
    assert _chat(server, "perro", key="mala").status_code == 401


def test_a2a_is_protected(server):
    assert httpx.get(f"{server}/a2a/translator/.well-known/agent-card.json").status_code == 401


def test_translation_goes_through_a2a_and_counts_both_agents(server):
    r = _chat(server, "como se dice perro")
    assert r.status_code == 200
    data = r.json()
    assert "peek'" in data["respuesta"]
    agentes = data["consumo"]["sesion"]["por_agente"]
    assert agentes["asistente"]["calls"] == 1 and agentes["traductor"]["calls"] == 1


def test_message_limit(server):
    codes = [_chat(server, "agua", sid="sesion-limite").status_code for _ in range(6)]
    assert codes[-1] == 429


def test_long_message_rejected(server):
    assert _chat(server, "x" * 1000).status_code == 400


def test_rate_limiter_blocks_bursts():
    from app.rate_limit import RateLimiter, client_ip

    rl = RateLimiter(per_minute=3, per_hour=100)
    assert [rl.check("1.2.3.4") for _ in range(3)] == [0, 0, 0]
    assert rl.check("1.2.3.4") > 0
    assert rl.check("5.6.7.8") == 0  # otra IP no se afecta
    assert client_ip({"x-forwarded-for": "10.0.0.1:51234, 1.1.1.1"}) == "10.0.0.1"
