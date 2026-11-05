"""Configuración centralizada.

Todo valor que dependa de la cuenta de Azure, del modelo o del despliegue se lee de
variables de entorno (o de un archivo .env en desarrollo). Cambiar de cuenta = cambiar el .env.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def _list(name: str) -> list[str]:
    return [v.strip() for v in os.getenv(name, "").split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    # --- Proveedor del modelo ---------------------------------------------------
    # "foundry": Microsoft Foundry con identidad de Entra (az login / identidad administrada).
    # "key": endpoint de Azure OpenAI del recurso Foundry con API key.
    # "fake": modelo simulado, sin costo, para pruebas locales.
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "foundry").lower())
    foundry_project_endpoint: str = field(default_factory=lambda: os.getenv("FOUNDRY_PROJECT_ENDPOINT", ""))
    azure_openai_endpoint: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_ENDPOINT", ""))
    azure_openai_api_key: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_API_KEY", ""))

    # Cada agente puede usar un despliegue distinto (ahorro: uno más barato para el asistente).
    assistant_model: str = field(default_factory=lambda: os.getenv("ASSISTANT_MODEL", os.getenv("FOUNDRY_MODEL", "gpt-5-mini")))
    translator_model: str = field(default_factory=lambda: os.getenv("TRANSLATOR_MODEL", os.getenv("FOUNDRY_MODEL", "gpt-5-mini")))

    # --- Ahorro de tokens -------------------------------------------------------
    reasoning_effort: str = field(default_factory=lambda: os.getenv("REASONING_EFFORT", "minimal"))
    max_output_tokens: int = field(default_factory=lambda: _int("MAX_OUTPUT_TOKENS", 600))
    history_turns: int = field(default_factory=lambda: _int("HISTORY_TURNS", 2))
    max_input_chars: int = field(default_factory=lambda: _int("MAX_INPUT_CHARS", 300))

    # --- A2A -----------------------------------------------------------------------
    port: int = field(default_factory=lambda: _int("PORT", 8000))
    translator_a2a_url: str = field(default_factory=lambda: os.getenv("TRANSLATOR_A2A_URL", ""))
    a2a_internal_key: str = field(default_factory=lambda: os.getenv("A2A_INTERNAL_KEY", ""))

    # --- Catálogo e internet --------------------------------------------------
    catalog_path: Path = field(default_factory=lambda: Path(os.getenv("CATALOG_PATH", str(BASE_DIR / "data" / "catalogo.md"))))
    allowed_sites: list[str] = field(default_factory=lambda: _list("ALLOWED_SITES"))

    # --- Consumo y costos ------------------------------------------------------
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", str(BASE_DIR / "data" / "runtime"))))
    price_input_per_1m: float = field(default_factory=lambda: _float("PRICE_INPUT_PER_1M", 0.25))
    price_output_per_1m: float = field(default_factory=lambda: _float("PRICE_OUTPUT_PER_1M", 2.00))
    currency: str = field(default_factory=lambda: os.getenv("PRICE_CURRENCY", "USD"))

    # --- Protección del acceso ---------------------------------------------
    app_access_key: str = field(default_factory=lambda: os.getenv("APP_ACCESS_KEY", ""))
    max_messages_per_session: int = field(default_factory=lambda: _int("MAX_MESSAGES_PER_SESSION", 30))
    max_tokens_per_session: int = field(default_factory=lambda: _int("MAX_TOKENS_PER_SESSION", 40000))
    max_tokens_per_day: int = field(default_factory=lambda: _int("MAX_TOKENS_PER_DAY", 300000))

    @property
    def translator_url(self) -> str:
        """URL A2A del traductor. Por defecto, la misma app (ruta interna)."""
        return (self.translator_a2a_url or f"http://127.0.0.1:{self.port}/a2a/translator").rstrip("/") + "/"


settings = Settings()
