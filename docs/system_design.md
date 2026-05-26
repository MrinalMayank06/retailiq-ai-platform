# System Design - RetailIQ AI Platform

## Input data
RetailIQ uses:
- `product_details.csv`
- `customer_data.csv`
- `order_data.csv`

## Core processing flow
Raw CSV -> cleaning -> feature engineering -> curated datasets -> ML training -> model artifacts -> vector store build -> FastAPI APIs -> MongoDB logs -> Power BI export

## Runtime components

### Machine learning
- demand forecasting
- anomaly detection
- customer segmentation

### Agents
- support agent
- sales agent
- analytics agent

### Retrieval
- Azure embeddings
- local JSON vector store
- product knowledge chunks

### Generation
- Azure chat deployment (`gpt-oss-120b`)

### Logging
- MongoDB Atlas

## Deployment
- local development with FastAPI
- Azure App Service for hosted runtime
- GitHub Actions for CI/CD
- Microsoft Fabric and Power BI as analytics proof layer
