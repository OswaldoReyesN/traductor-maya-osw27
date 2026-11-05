---
agent: azure-foundry
description: Guía para mover la app a otra suscripción o cuenta de Azure sin tocar el código.
---
Quiero usar otra cuenta/suscripción de Azure: ${input:cuenta:Nombre o id de la nueva suscripción}

1. Revisa en esa suscripción qué modelos de chat económicos tienen cuota (`az cognitiveservices usage list -l <region>`).
2. Propón el modelo y la región más baratos y pide confirmación.
3. Indica qué variables de `.env` / App Service cambian (`FOUNDRY_PROJECT_ENDPOINT`, `ASSISTANT_MODEL`, `TRANSLATOR_MODEL`, precios).
4. Recuerda reasignar el rol **Azure AI User** a la identidad que use la app.
No modifiques código.
