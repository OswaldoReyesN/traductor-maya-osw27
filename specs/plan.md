# Plan técnico

- **Modelo:** `gpt-5-mini` (despliegue Global Standard en Foundry). `gpt-5.4-nano` no tenía cuota en Azure for Students; se cambia con una variable.
- **Agentes:** Microsoft Agent Framework (`Agent` + `FoundryChatClient`).
- **A2A:** `agent-framework-a2a` — `A2AExecutor` publica al traductor; `A2AAgent` es el cliente del asistente. Ambos en la misma app (ruta `/a2a/translator`), dirección configurable.
- **Catálogo:** búsqueda determinista en Python (sin tokens). El modelo solo interpreta y redacta.
- **Consumo:** subclase `TrackedAgent` registra `usage_details` en `usage.json`; el id de sesión viaja en los metadatos A2A.
- **Web:** FastAPI + una página HTML con JS mínimo.
- **Hospedaje:** App Service Linux F1 + identidad administrada (rol *Foundry User*).
- **Pruebas:** pytest con modelo simulado (`LLM_PROVIDER=fake`).
