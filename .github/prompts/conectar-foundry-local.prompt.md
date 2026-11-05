---
agent: agent
description: Conecta la app local al modelo real de Microsoft Foundry usando az login (sin API keys).
---
Conecta la app local a Microsoft Foundry:

1. Verifica que Azure CLI esté instalado (`az version`). Si no, dime cómo instalarlo en mi sistema y detente.
2. Ejecuta `az login` y luego `az account show --query name -o tsv` para confirmar que la suscripción es **Azure for Students**.
3. Obtén el endpoint del proyecto: es `https://osw-ariel-ia-0227-resource.services.ai.azure.com/api/projects/osw-ariel-ia-0227` (confírmalo en Foundry → Home → *Project endpoint*).
4. Asigna a mi usuario el rol **Azure AI User** sobre el recurso `osw-ariel-ia-0227-resource` del grupo `rg-osw_ariel-ia-3954` (pídeme confirmación antes).
5. En `.env` pon `LLM_PROVIDER=foundry`, `FOUNDRY_PROJECT_ENDPOINT=<endpoint>`, `ASSISTANT_MODEL=gpt-5-mini`, `TRANSLATOR_MODEL=gpt-5-mini`.
6. Arranca la app y prueba: "¿cómo se dice perro en maya?". Muéstrame la respuesta y el consumo de tokens.
