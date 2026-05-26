# Deployment Steps - RetailIQ AI Platform

## 1. Push code to GitHub
Ensure:
- tests pass
- vector store build works locally
- workflow file is committed

## 2. GitHub Actions deploys to Azure App Service
The CI/CD workflow should:
- checkout code
- package application
- deploy to Azure App Service using publish profile

## 3. Configure Azure App Service
Set:
- startup command
- required App Settings
- embedding endpoint variables
- chat endpoint variables
- MongoDB connection string

## 4. Restart App Service
After configuration changes:
- Save
- Restart
- wait for startup

## 5. Validate deployment
Test in this order:

1. `GET /health`
2. `GET /api/status`
3. `GET /docs`
4. `POST /api/agent` with support intent
5. `POST /api/demand-forecast`
6. `POST /api/anomaly-check`
7. `GET /api/logs`

## 6. Common validation goal
A successful deployment should confirm:
- app health is green
- Azure chat is configured
- Azure embeddings are configured
- local vector store retrieval is active
- MongoDB logs are working

## 7. If errors appear
Check:
- Azure Log Stream
- missing environment variables
- wrong embedding endpoint
- wrong chat endpoint
- missing vector store artifact path
- startup command mismatch
