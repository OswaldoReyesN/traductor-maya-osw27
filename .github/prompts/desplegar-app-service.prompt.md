---
agent: azure-foundry
description: Despliega la app en Azure App Service (plan F1 gratuito) con identidad administrada hacia Foundry.
---
Despliega el Traductor Maya en Azure App Service con el menor costo posible. Pide confirmación antes de crear recursos.

Datos: grupo `rg-osw_ariel-ia-3954`, región `northcentralus`, recurso Foundry `osw-ariel-ia-0227-resource`,
endpoint `https://osw-ariel-ia-0227-resource.services.ai.azure.com/api/projects/osw-ariel-ia-0227`, modelo `gpt-5-mini`.

1. `az webapp up` con runtime `PYTHON:3.12`, sku `F1`, nombre `traductor-maya-<sufijo>`.
2. Activa la identidad administrada del sistema y dale el rol **Azure AI User** sobre el recurso Foundry.
3. Configura las variables (ver `.env.example`): `LLM_PROVIDER=foundry`, endpoint, modelos, `DATA_DIR=/home/data`, `PORT=8000`,
   `SCM_DO_BUILD_DURING_DEPLOYMENT=true`, y genera valores aleatorios largos para `A2A_INTERNAL_KEY` y `APP_ACCESS_KEY`
   (dime la `APP_ACCESS_KEY` solo a mí en el chat; no la escribas en archivos).
4. Comando de arranque: `startup.sh`.
5. Prueba `https://<app>.azurewebsites.net/healthz` y una traducción. Muéstrame los logs si falla (`az webapp log tail`).
