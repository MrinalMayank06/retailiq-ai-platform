# Azure Setup Guide - Chat Model, Embedding Model, API Keys, and Endpoints

This file explains how to create the required Azure resources and where to get the API key, endpoint, and deployment names needed by RetailIQ.

## 1. What RetailIQ needs from Azure

RetailIQ needs two AI capabilities:

1. **Azure chat deployment**
   - used by support, sales, and analytics agents
   - recommended deployment name in this project: `gpt-oss-120b`

2. **Azure embedding deployment**
   - used to create semantic vectors for product knowledge and support queries
   - recommended deployment name in this project: `text-embedding-3-large`

## 2. Recommended resource split

Use separate Azure resources if needed:

- **Chat / Foundry-style resource**
  - for the chat model endpoint
- **Azure OpenAI / Cognitive Services style resource**
  - for the embedding deployment endpoint

## 3. Create the chat model deployment

### Option A — Microsoft Foundry portal flow
1. Sign in to the Azure portal.
2. Create or open the Azure AI / Foundry resource or project you plan to use for chat.
3. Open the Foundry portal experience.
4. Go to **Build** or **Model catalog**.
5. Search for the chat model you want to use.
6. Select the model.
7. Choose **Deploy** or **Use this model**.
8. Create a deployment.
9. After deployment succeeds, copy:
   - endpoint / target URI
   - API key
   - deployment name

### Recommended chat model
- `gpt-oss-120b`

## 4. Create the embedding deployment

1. Open the Azure resource used for embeddings.
2. Go to the deployments area.
3. Search for an embedding model.
4. Select and deploy the embedding model.
5. After deployment succeeds, copy:
   - embedding endpoint
   - embedding API key
   - deployment name

### Recommended embedding model
- `text-embedding-3-large`

## 5. What values you need to collect

### Chat values
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_BASE_URL`
- `AZURE_OPENAI_CHAT_MODEL`
- `AZURE_OPENAI_MODEL`

### Embedding values
- `AZURE_OPENAI_EMBEDDING_API_KEY`
- `AZURE_OPENAI_EMBEDDING_BASE_URL`
- `AZURE_OPENAI_EMBEDDING_MODEL`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
- `AZURE_OPENAI_EMBEDDING_API_VERSION`

## 6. Example local `.env`

```env
APP_NAME=RetailIQ AI Platform
APP_ENV=local
APP_HOST=127.0.0.1
APP_PORT=8000

MONGODB_URI=your_mongodb_uri
MONGODB_DB=retailiq

AZURE_OPENAI_API_KEY=your_chat_key
AZURE_OPENAI_BASE_URL=https://your-chat-resource.services.ai.azure.com/openai/v1/
AZURE_OPENAI_CHAT_MODEL=gpt-oss-120b
AZURE_OPENAI_MODEL=gpt-oss-120b

AZURE_OPENAI_EMBEDDING_API_KEY=your_embedding_key
AZURE_OPENAI_EMBEDDING_BASE_URL=https://your-embedding-resource.cognitiveservices.azure.com/
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-large
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
AZURE_OPENAI_EMBEDDING_API_VERSION=2024-02-01

PRODUCT_KNOWLEDGE_STORE_PATH=artifacts/knowledge/product_knowledge_embeddings.json
```

## 7. Example Azure App Service configuration

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

## 8. Validation order after Azure configuration

1. Deploy code through GitHub Actions
2. Set App Service environment variables
3. Restart App Service
4. Open:
   - `/health`
   - `/api/status`
   - `/docs`
5. Test support agent:
   - `/api/agent` with `support`

## 9. Common mistakes to avoid

- using chat endpoint values in embedding settings
- using embedding endpoint values in chat settings
- forgetting to restart App Service after changing settings
- forgetting `PRODUCT_KNOWLEDGE_STORE_PATH`
- keeping old Chroma / MiniLM variables in final Azure config
