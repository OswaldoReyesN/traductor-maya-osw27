---
agent: agent
description: Inicializa git y publica el proyecto en un repositorio público de GitHub, verificando que no se suban secretos.
---
Publica este proyecto en GitHub como repositorio **público**:

1. Antes de nada, revisa que `.env` esté en `.gitignore` y busca en los archivos que se van a subir cualquier clave, token o contraseña (`git grep -nIE "key|secret|password|token"` tras `git add`). Si encuentras algo sospechoso, detente y avísame.
2. Si la carpeta no es repo: `git init -b main`, `git add .`, commit "Traductor Maya v1".
3. Crea el repo público `traductor-maya` en mi cuenta (con la extensión de GitHub de VS Code o `gh repo create traductor-maya --public --source . --push`).
4. Dame la URL del repositorio.
