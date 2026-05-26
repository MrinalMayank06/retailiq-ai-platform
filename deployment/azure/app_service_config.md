# Azure App Service Configuration - RetailIQ AI Platform

## Recommended deployment target
- Azure App Service
- Linux
- Python 3.12

## Startup command

```bash
gunicorn -w 1 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 src.api.main:app --timeout 180
```

## Required App Settings

```text
APP_NAME=RetailIQ AI Platform
APP_ENV=prod
APP_HOST=0.0.0.0
APP_PORT=8000
WEBSITES_PORT=8000
SCM_DO_BUILD_DURING_DEPLOYMENT=true
WEBSITES_CONTAINER_START_TIME_LIMIT=1800

MONGODB_URI=<atlas connection string>
MONGODB_DB=retailiq

AZURE_OPENAI_API_KEY=<chat key>
AZURE_OPENAI_BASE_URL=https://<chat-resource>.services.ai.azure.com/openai/v1/
AZURE_OPENAI_CHAT_MODEL=gpt-oss-120b
AZURE_OPENAI_MODEL=gpt-oss-120b

AZURE_OPENAI_EMBEDDING_API_KEY=<embedding key>
AZURE_OPENAI_EMBEDDING_BASE_URL=https://<embedding-resource>.cognitiveservices.azure.com/
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-large
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
AZURE_OPENAI_EMBEDDING_API_VERSION=2024-02-01

PRODUCT_KNOWLEDGE_STORE_PATH=/home/site/wwwroot/artifacts/knowledge/product_knowledge_embeddings.json
```

## Final runtime retrieval design
RetailIQ uses:
- Azure embeddings
- local JSON vector store
- Azure chat generation

It does not use Azure AI Search in the final runtime path.

## Legacy note
`scripts/build_chroma_store.py` remains as a legacy script filename for compatibility, but it now builds the local JSON vector store using Azure embeddings.
