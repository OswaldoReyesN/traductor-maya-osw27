# Instrucciones del proyecto para GitHub Copilot

Proyecto: **Traductor Maya** — chat web (Python, FastAPI) con dos agentes de Microsoft Agent Framework (asistente y traductor) comunicados por **A2A**, usando un modelo de **Microsoft Foundry**. Lee `specs/spec.md` y `docs/ARQUITECTURA.md` antes de cambios grandes.

## Reglas
- Python 3.12, código simple y comentado en español.
- **Nunca** pongas secretos, endpoints ni nombres de cuenta en el código: todo va en `app/config.py` leyendo variables de entorno, y se documenta en `.env.example`.
- El traductor **solo** traduce con `data/catalogo.md` vía `buscar_en_catalogo`. No agregues lógica que permita al modelo traducir de memoria.
- Prioridad **ahorro de tokens**: no reenvíes más historial, no aumentes `MAX_OUTPUT_TOKENS` ni metas el catálogo completo en el prompt sin justificarlo.
- Sin base de datos: el consumo vive en `app/usage_store.py`.
- Mantén mínimas las dependencias (`requirements.txt` con versiones fijas).
- Toda nueva función lleva prueba en `tests/` que corra con `LLM_PROVIDER=fake` (sin costo).
- Si cambias el comportamiento, actualiza `docs/FUNCIONAL.md` o `docs/ARQUITECTURA.md` en lenguaje sencillo.

## Comandos
- Instalar: `pip install -r requirements.txt -r requirements-dev.txt`
- Ejecutar: `python -m uvicorn app.main:app --reload`
- Probar: `python -m pytest`
