# Traductor Maya 🌽

Chat web con IA que traduce **palabras sueltas** entre **español, inglés y maya yucateco**.
Proyecto del curso *Fundamentos de IA con Tecnologías Microsoft* (Microsoft Foundry).

- Dos agentes que se comunican por **A2A (Agent-to-Agent)**: un **asistente** que conversa y un **traductor** especializado.
- El traductor solo usa el **catálogo oficial** [`data/catalogo.md`](data/catalogo.md). No inventa traducciones.
- Panel de **consumo de tokens** (sesión, día e histórico) con **costo estimado**.
- Sin base de datos: el consumo se guarda en un archivo JSON.
- Todo es configurable con variables de entorno: puedes cambiar de cuenta de Azure sin tocar el código.

📘 Documentación: [Guía funcional](docs/FUNCIONAL.md) · [Arquitectura](docs/ARQUITECTURA.md) · [Especificación](specs/spec.md)

## Probar en 2 minutos (sin Azure, sin costo)

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # y pon LLM_PROVIDER=fake
python -m uvicorn app.main:app --reload
```

Abre http://localhost:8000. Con `LLM_PROVIDER=fake` el modelo es simulado; la búsqueda en el catálogo y el A2A son reales.

## Usar Microsoft Foundry

1. En `.env`: `LLM_PROVIDER=foundry`, `FOUNDRY_PROJECT_ENDPOINT` y el nombre del despliegue (`ASSISTANT_MODEL`, `TRANSLATOR_MODEL`).
2. Inicia sesión con `az login` (tu usuario necesita el rol **Azure AI User** en el recurso Foundry).
3. Ejecuta la app igual que arriba.

## Pruebas

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Desplegar en Azure App Service

Ver [docs/ARQUITECTURA.md § Despliegue](docs/ARQUITECTURA.md#despliegue-en-azure-app-service) o el prompt de Copilot [`.github/prompts/desplegar-app-service.prompt.md`](.github/prompts/desplegar-app-service.prompt.md).

## Trabajar con GitHub Copilot

- Reglas del proyecto: [`.github/copilot-instructions.md`](.github/copilot-instructions.md)
- Agentes: [`.github/agents/`](.github/agents) · Prompts listos para usar: [`.github/prompts/`](.github/prompts) (en el chat de Copilot escribe `/` y el nombre del prompt).
