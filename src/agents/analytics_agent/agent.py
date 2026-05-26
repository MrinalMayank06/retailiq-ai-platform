from __future__ import annotations

import json
from datetime import datetime

import pandas as pd

from src.common.constants import DATA_CURATED_DIR, ARTIFACTS_DIR
from src.agents.shared.llm_client import get_llm_client
from src.database.crud import insert_one


def get_dashboard_metrics() -> dict:
    master_path = DATA_CURATED_DIR / "master_sales_dataset.csv"
    customer_path = DATA_CURATED_DIR / "customer_segments.csv"
    anomaly_path = DATA_CURATED_DIR / "anomaly_dataset.csv"
    metrics_path = ARTIFACTS_DIR / "metrics" / "training_metrics.json"

    if not master_path.exists():
        return {
            "message": "Training not completed yet. Run training first."
        }

    master_df = pd.read_csv(master_path)

    metrics = {
        "total_orders": int(master_df["order_id"].nunique()),
        "total_products": int(master_df["product_id"].nunique()),
        "total_customers": int(master_df["customer_id"].nunique()),
        "total_revenue": round(float(master_df["total_amount"].sum()), 2),
        "average_order_value": round(float(master_df["total_amount"].mean()), 2),
    }

    if "category" in master_df.columns:
        metrics["top_categories"] = {
            str(k): round(float(v), 2)
            for k, v in master_df.groupby("category")["total_amount"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .items()
        }

    if anomaly_path.exists():
        anomaly_df = pd.read_csv(anomaly_path)

        if "anomaly_flag" in anomaly_df.columns:
            metrics["labeled_anomaly_count"] = int(anomaly_df["anomaly_flag"].sum())
            metrics["labeled_anomaly_rate"] = round(float(anomaly_df["anomaly_flag"].mean()), 4)

    if customer_path.exists():
        customer_df = pd.read_csv(customer_path)

        if "cluster" in customer_df.columns:
            cluster_counts = customer_df["cluster"].value_counts().to_dict()
            metrics["customer_clusters"] = {
                str(k): int(v)
                for k, v in cluster_counts.items()
            }

    if metrics_path.exists():
        with open(metrics_path, "r", encoding="utf-8") as file:
            training_metrics = json.load(file)

        metrics["model_metrics"] = training_metrics.get("metrics", {})

    return metrics


def generate_analytics_insight(question: str | None = None) -> dict:
    metrics = get_dashboard_metrics()

    system_prompt = """
You are RetailIQ Analytics Agent.
You explain dashboard metrics, model performance, anomaly trends, and customer segmentation in business language.
Be concise, analytical, and suitable for an enterprise retail stakeholder.
"""

    user_prompt = f"""
User Question:
{question or "Summarize overall retail business performance."}

Dashboard and Model Metrics:
{json.dumps(metrics, indent=2)}

Generate:
1. Executive summary
2. Revenue insight
3. Anomaly insight
4. Customer segmentation insight
5. Model performance interpretation
6. Recommended business actions
"""

    llm = get_llm_client()

    insight = llm.chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.25,
        max_tokens=900,
    )

    response = {
        "question": question,
        "metrics": metrics,
        "insight": insight,
        "agent": "analytics_agent",
        "created_at": datetime.utcnow().isoformat(),
    }

    try:
        insert_one("chat_logs", response)
    except Exception:
        pass

    return response