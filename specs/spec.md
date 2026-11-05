# Especificación — Traductor Maya (v1)

## Objetivo
Chat web con IA que traduce palabras sueltas entre español, inglés y maya yucateco, construido con Microsoft Foundry, pequeño pero preparado para crecer.

## Requerimientos funcionales
| ID | Requerimiento |
|---|---|
| RF1 | El usuario escribe en un chat y recibe respuesta del agente **asistente**. |
| RF2 | El asistente delega cada traducción al agente **traductor** mediante **A2A**. |
| RF3 | Traducción de palabras sueltas español ↔ maya (inglés desactivado por ahora, configurable). |
| RF4 | El traductor usa el catálogo oficial `.md` (500 palabras); si no está, consulta solo las fuentes de `ALLOWED_SOURCES` y lo indica; si tampoco, "no disponible". |
| RF4b | Las respuestas incluyen significado y frase de ejemplo, con tono cálido. |
| RF5 | Peticiones que no son traducción se redirigen amablemente. |
| RF6 | Panel con tokens de la sesión (por agente), del día e históricos, con costo estimado. |
| RF7 | Historial solo durante la sesión. |
| RF8 | Clave de acceso y límites por mensaje, sesión, día e IP (anti-bots). |
| RF8b | Indicador visual mientras el modelo trabaja. |
| RF9 | Sin internet, salvo URLs listadas en `ALLOWED_SOURCES`. |

## Requerimientos no funcionales
| ID | Requerimiento |
|---|---|
| RNF1 | Python; frontend muy sencillo (FastAPI + HTML). |
| RNF2 | Todo configurable por variables de entorno; cuenta de Azure intercambiable. |
| RNF3 | Prioridad: mínimo consumo (modelo económico, contexto corto, sin BD). |
| RNF4 | Despliegue ligero en Azure App Service. |
| RNF5 | Repositorio público sin secretos. |
| RNF6 | Documentación funcional y técnica comprensible para principiantes. |

## Fuera de alcance (v1)
Traducción de frases, interfaz bilingüe, base de datos, autenticación de usuarios individuales.
