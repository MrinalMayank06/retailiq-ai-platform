from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.api.middleware.error_handler import generic_exception_handler
from src.api.utils.response_formatter import success_response
from src.common.constants import DATA_CURATED_DIR, DATA_RAW_DIR, MODELS_DIR
from src.common.settings import get_settings
from src.database.crud import insert_one
from src.database.mongo_client import get_db
from src.ml.inference.predict import detect_anomaly, predict_demand
from src.agents.analytics_agent.agent import (
    generate_analytics_insight,
    get_dashboard_metrics,
)
from src.agents.mcp.mcp_orchestrator import mcp_orchestrator
from src.agents.sales_agent.agent import generate_sales_insight
from src.agents.support_agent.rag_pipeline import answer_support_question


settings = get_settings()

OPENAPI_TAGS = [
    {
        "name": "Platform Operations",
        "description": "Health checks and platform readiness.",
    },
    {
        "name": "Forecasting",
        "description": "Demand forecasting APIs for retail planning.",
    },
    {
        "name": "Risk Monitoring",
        "description": "Anomaly and transaction risk evaluation APIs.",
    },
    {
        "name": "Retail Assistant",
        "description": "Unified AI assistant for support, sales, and analytics.",
    },
    {
        "name": "Observability",
        "description": "Recent operational logs and audit-friendly outputs.",
    },
]

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "RetailIQ AI Platform backend with ML, Azure embedding powered local JSON "
        "vector retrieval, Azure chat, MCP orchestration, MongoDB logs, and Azure deployment."
    ),
    openapi_tags=OPENAPI_TAGS,
)

app.add_exception_handler(Exception, generic_exception_handler)


class DemandForecastRequest(BaseModel):
    product_id: str = Field(..., examples=["P001"])
    forecast_date: str = Field(..., examples=["2026-06-01"])


class AnomalyCheckRequest(BaseModel):
    quantity: float = Field(..., gt=0, examples=[80])
    price: float = Field(..., gt=0, examples=[15000])
    discount_pct: float = Field(0, ge=0, examples=[0])
    promotion_flag: int = Field(0, ge=0, le=1, examples=[0])


class UnifiedAgentRequest(BaseModel):
    intent: Literal["support", "sales", "analytics"] = Field(
        ...,
        examples=["support"],
        description="support = product Q&A, sales = forecast insight, analytics = business summary",
    )
    question: str | None = Field(None, examples=["What is the return policy for P001?"])
    product_id: str | None = Field(None, examples=["P001"])
    forecast_date: str | None = Field(None, examples=["2026-06-01"])


def _resolve_store_artifact_path() -> Path:
    store_path = Path(settings.product_knowledge_store_path)

    if not store_path.is_absolute():
        project_root = Path(__file__).resolve().parents[2]
        store_path = project_root / store_path

    return store_path


def _safe_insert_one(collection_name: str, document: dict[str, Any]) -> bool:
    try:
        insert_one(collection_name, document)
        return True
    except Exception:
        return False


def _safe_dashboard_metrics() -> dict[str, Any]:
    try:
        return get_dashboard_metrics()
    except Exception as exc:
        return {
            "status": "unavailable",
            "error": str(exc),
        }


@app.get("/", include_in_schema=False)
def root():
    return {
        "success": True,
        "message": "RetailIQ API is running. Open /docs for Swagger UI.",
    }


@app.get("/health", tags=["Platform Operations"], summary="Service Health Check")
def health():
    return {
        "success": True,
        "message": "RetailIQ API is healthy",
        "data": {
            "env": settings.app_env,
            "app_name": settings.app_name,
        },
    }


@app.get("/api/status", tags=["Platform Operations"], summary="Platform Readiness Status")
def platform_status():
    raw_files = {
        "product_details": (DATA_RAW_DIR / "product_details.csv").exists(),
        "customer_data": (DATA_RAW_DIR / "customer_data.csv").exists(),
        "order_data": (DATA_RAW_DIR / "order_data.csv").exists(),
    }

    curated_files = {
        "master_sales_dataset": (DATA_CURATED_DIR / "master_sales_dataset.csv").exists(),
        "demand_dataset": (DATA_CURATED_DIR / "demand_dataset.csv").exists(),
        "anomaly_dataset": (DATA_CURATED_DIR / "anomaly_dataset.csv").exists(),
        "customer_segments": (DATA_CURATED_DIR / "customer_segments.csv").exists(),
    }

    model_files = {
        "demand_model": (MODELS_DIR / "demand_model.joblib").exists(),
        "anomaly_model": (MODELS_DIR / "anomaly_model.joblib").exists(),
        "clustering_model": (MODELS_DIR / "clustering_model.joblib").exists(),
    }

    azure_chat_configured = bool(
        settings.azure_openai_api_key
        and settings.azure_openai_base_url
        and (settings.azure_openai_chat_model or settings.azure_openai_model)
    )

    azure_embedding_configured = bool(
        settings.azure_openai_embedding_api_key
        and settings.azure_openai_embedding_base_url
        and settings.azure_openai_embedding_deployment
    )

    store_path = _resolve_store_artifact_path()
    store_artifact_exists = store_path.exists()
    product_file_ready = raw_files["product_details"]

    azure_components = {
        "azure_foundry_chat_configured": azure_chat_configured,
        "azure_chat_configured": azure_chat_configured,
        "azure_embedding_configured": azure_embedding_configured,
        "azure_app_service_ready": True,
    }

    retrieval_components = {
        "rag_backend": "azure_embedding_local_json_store",
        "knowledge_source": "data/raw/product_details.csv",
        "embedding_model": settings.azure_openai_embedding_model,
        "embedding_deployment": settings.azure_openai_embedding_deployment,
        "vector_db": "local_json_vector_store",
        "store_artifact": settings.product_knowledge_store_path,
        "store_artifact_resolved_path": str(store_path),
        "store_artifact_exists": store_artifact_exists,
        "retrieval_ready": bool(
            product_file_ready
            and azure_embedding_configured
            and store_artifact_exists
        ),
    }

    return success_response(
        "RetailIQ platform status fetched successfully",
        {
            "raw_files": raw_files,
            "curated_files": curated_files,
            "model_files": model_files,
            "azure_components": azure_components,
            "retrieval_components": retrieval_components,
            "mcp_tools": mcp_orchestrator.list_tools(),
            "dashboard_summary": _safe_dashboard_metrics(),
        },
    )


@app.post("/api/demand-forecast", tags=["Forecasting"], summary="Generate Demand Forecast")
def demand_forecast(request: DemandForecastRequest):
    result = predict_demand(
        product_id=request.product_id,
        forecast_date=request.forecast_date,
    )

    _safe_insert_one(
        "predictions",
        {
            "type": "demo_demand_forecast",
            "created_at": datetime.utcnow().isoformat(),
            **result,
        },
    )

    return success_response(
        "Demand forecast generated successfully",
        result,
    )


@app.post("/api/anomaly-check", tags=["Risk Monitoring"], summary="Evaluate Transaction Risk")
def anomaly_check(request: AnomalyCheckRequest):
    result = detect_anomaly(
        quantity=request.quantity,
        price=request.price,
        discount_pct=request.discount_pct,
        promotion_flag=request.promotion_flag,
    )

    _safe_insert_one(
        "predictions",
        {
            "type": "demo_anomaly_check",
            "created_at": datetime.utcnow().isoformat(),
            **result,
        },
    )

    return success_response(
        "Anomaly check completed successfully",
        result,
    )


@app.post("/api/agent", tags=["Retail Assistant"], summary="Retail Intelligence Assistant")
def unified_agent(request: UnifiedAgentRequest):
    if request.intent == "support":
        if not request.question or not request.question.strip():
            raise HTTPException(
                status_code=400,
                detail="question is required for support intent",
            )

        result = answer_support_question(request.question.strip())

        return success_response(
            "Support agent response generated successfully",
            result,
        )

    if request.intent == "sales":
        if not request.product_id or not request.forecast_date:
            raise HTTPException(
                status_code=400,
                detail="product_id and forecast_date are required for sales intent",
            )

        result = generate_sales_insight(
            product_id=request.product_id,
            forecast_date=request.forecast_date,
        )

        return success_response(
            "Sales agent insight generated successfully",
            result,
        )

    if request.intent == "analytics":
        result = generate_analytics_insight(request.question)

        return success_response(
            "Analytics agent insight generated successfully",
            result,
        )

    raise HTTPException(status_code=400, detail="Invalid intent")


@app.get("/api/logs", tags=["Observability"], summary="Recent Platform Activity")
def latest_logs(limit: int = 5):
    try:
        db = get_db()
    except Exception:
        db = None

    if db is None:
        return success_response(
            "MongoDB connection unavailable. Returning empty activity logs.",
            {
                "chat_logs": [],
                "prediction_logs": [],
                "training_logs": [],
            },
        )

    try:
        chat_logs = list(
            db["chat_logs"].find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
        )
        predictions = list(
            db["predictions"].find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
        )
        training_runs = list(
            db["training_runs"].find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
        )
    except Exception:
        chat_logs = []
        predictions = []
        training_runs = []

    return success_response(
        "Latest MongoDB logs fetched successfully",
        {
            "chat_logs": chat_logs,
            "prediction_logs": predictions,
            "training_logs": training_runs,
        },
    )