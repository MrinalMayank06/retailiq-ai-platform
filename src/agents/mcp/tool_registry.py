from __future__ import annotations

from typing import Any

from src.agents.analytics_agent.agent import get_dashboard_metrics
from src.agents.support_agent.vector_store import (
    ProductKnowledgeStore,
    rebuild_product_knowledge_store,
)
from src.ml.inference.predict import (
    detect_anomaly,
    predict_demand,
    segment_customers,
)


def _require(arguments: dict[str, Any], required_keys: list[str]) -> None:
    missing = [
        key
        for key in required_keys
        if key not in arguments or arguments[key] in [None, ""]
    ]

    if missing:
        raise ValueError(
            f"Missing required argument(s): {missing}. Received arguments: {arguments}"
        )


def demand_forecast_tool(arguments: dict[str, Any]) -> dict:
    _require(arguments, ["product_id", "forecast_date"])

    return predict_demand(
        product_id=arguments["product_id"],
        forecast_date=arguments["forecast_date"],
    )


def anomaly_detection_tool(arguments: dict[str, Any]) -> dict:
    _require(arguments, ["quantity", "price"])

    return detect_anomaly(
        quantity=arguments["quantity"],
        price=arguments["price"],
        discount_pct=arguments.get("discount_pct", 0),
        promotion_flag=arguments.get("promotion_flag", 0),
    )


def customer_segment_tool(arguments: dict[str, Any] | None = None) -> dict:
    segments = segment_customers()

    return {
        "total_customers": len(segments),
        "sample_segments": segments[:10],
    }


def dashboard_metrics_tool(arguments: dict[str, Any] | None = None) -> dict:
    try:
        return get_dashboard_metrics()
    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
        }


def product_search_tool(arguments: dict[str, Any]) -> dict:
    _require(arguments, ["query"])

    query = arguments["query"]

    try:
        store = ProductKnowledgeStore()

        results = store.search(
            query=query,
            top_k=int(arguments.get("top_k", 3)),
        )

        return {
            "status": "success",
            "query": query,
            "results": results,
            "source": "azure_embedding_local_json_store",
            "retrieval_backend": "local_json_vector_store",
            "embedding_model": "text-embedding-3-large",
        }

    except Exception as exc:
        return {
            "status": "failed",
            "query": query,
            "results": [],
            "error": str(exc),
            "source": "azure_embedding_local_json_store",
            "retrieval_backend": "local_json_vector_store",
            "embedding_model": "text-embedding-3-large",
        }


def rebuild_product_knowledge_tool(arguments: dict[str, Any] | None = None) -> dict:
    try:
        result = rebuild_product_knowledge_store()

        return {
            "status": "success",
            **result,
            "source": "azure_embedding_local_json_store",
            "retrieval_backend": "local_json_vector_store",
        }

    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
            "source": "azure_embedding_local_json_store",
            "retrieval_backend": "local_json_vector_store",
        }


TOOL_REGISTRY = {
    "demand_forecast_tool": demand_forecast_tool,
    "anomaly_detection_tool": anomaly_detection_tool,
    "customer_segment_tool": customer_segment_tool,
    "dashboard_metrics_tool": dashboard_metrics_tool,
    "product_search_tool": product_search_tool,
    "rebuild_product_knowledge_tool": rebuild_product_knowledge_tool,
}