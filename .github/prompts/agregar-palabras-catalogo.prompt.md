---
agent: agent
description: Agrega o importa palabras al catálogo oficial data/catalogo.md validando el formato.
---
Quiero actualizar el catálogo oficial `data/catalogo.md` con estas palabras: ${input:palabras:Pega aquí la lista o la tabla}

Reglas:
- Mantén la tabla `| Español | English | Maya | Categoría | Notas |`.
- **No inventes ni corrijas traducciones al maya**: usa exactamente lo que te doy. Si falta un dato, deja la celda vacía y avísame.
- Saltillo con apóstrofo recto `'`; sinónimos con `/`.
- Avisa si hay palabras duplicadas.
- Quita el aviso de "contenido de ejemplo" cuando el catálogo ya sea el oficial.
- Al terminar, ejecuta `python -m pytest tests/test_catalog.py` y dime cuántas palabras tiene el catálogo.
