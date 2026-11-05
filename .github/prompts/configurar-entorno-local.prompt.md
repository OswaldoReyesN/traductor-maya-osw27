---
agent: agent
description: Prepara el entorno local (venv, dependencias, .env) y prueba la app con el modelo simulado.
---
Prepara el entorno local del proyecto Traductor Maya en esta carpeta:

1. Verifica que haya Python 3.12 o superior (`python3 --version`).
2. Crea el entorno virtual `.venv` y actívalo.
3. Instala `requirements.txt` y `requirements-dev.txt`.
4. Si no existe `.env`, cópialo desde `.env.example` y pon `LLM_PROVIDER=fake`. No escribas ninguna clave real.
5. Ejecuta `python -m pytest` y muéstrame el resultado.
6. Arranca la app con `python -m uvicorn app.main:app --reload` y dime la URL para abrirla.
