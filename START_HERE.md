# START HERE

RetailIQ AI Platform quickstart guide.

## 1. Raw input files
Make sure these files exist:

- `data/raw/product_details.csv`
- `data/raw/customer_data.csv`
- `data/raw/order_data.csv`

## 2. Create virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3. Configure `.env`

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

## 4. Train models

```powershell
python -m scripts.run_training
```

## 5. Build local vector store

```powershell
python -m scripts.build_chroma_store
```

## 6. Run tests

```powershell
python -m pytest -q
```

## 7. Run API

```powershell
python -m scripts.run_api
```

Open:
- `http://127.0.0.1:8000/docs`

## 8. Validate in this order
1. `/health`
2. `/api/status`
3. `/api/demand-forecast`
4. `/api/anomaly-check`
5. `/api/agent`
6. `/api/logs`

## 9. Azure only after local success
After local success:
- push to GitHub
- let GitHub Actions deploy to Azure App Service
- configure App Service environment variables
- restart App Service
- validate live endpoints
