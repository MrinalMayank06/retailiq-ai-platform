# Security Considerations - RetailIQ AI Platform

## Local development
- Secrets are stored in `.env`.
- `.env` is excluded from Git.
- Secrets are not hardcoded in source code.
- Temporary runtime artifacts should not be committed accidentally.

## Azure deployment
- Azure App Service uses environment variables for runtime configuration.
- Azure Key Vault is the recommended next security improvement.
- Managed identity can be added later for secret access hardening.

## Sensitive values

| Secret | Purpose |
|---|---|
| `MONGODB_URI` | MongoDB Atlas connection |
| `AZURE_OPENAI_API_KEY` | Azure chat access |
| `AZURE_OPENAI_EMBEDDING_API_KEY` | Azure embedding access |

## Rotation guidance
If exposed, rotate:
1. MongoDB secret
2. Azure chat key
3. Azure embedding key
4. update App Service settings
5. restart App Service

## Repository hygiene
Do not commit:
- `.env`
- runtime caches
- temporary logs
- `__pycache__`
- old or unused runtime artifacts
