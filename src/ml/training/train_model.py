from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import pandas as pd
import joblib
import numpy as np
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error,
    silhouette_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)
from sklearn.model_selection import train_test_split

from src.common.logger import get_logger
from src.database.crud import insert_one
from src.ml.data_pipeline.loader import load_raw_data
from src.ml.data_pipeline.feature_engineering import (
    build_master_table,
    build_demand_dataset,
    build_anomaly_dataset,
    build_customer_dataset,
)
from src.ml.models.regression import build_demand_model
from src.ml.models.anomaly_detection import build_anomaly_model
from src.ml.models.clustering import build_clustering_model

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_DIR = PROJECT_ROOT / "artifacts" / "models"
METRICS_DIR = PROJECT_ROOT / "artifacts" / "metrics"
CURATED_DIR = PROJECT_ROOT / "data" / "curated"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)
CURATED_DIR.mkdir(parents=True, exist_ok=True)


def _rmse(y_true, y_pred) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def train_demand_model(demand_df):
    demand_features = [
        "product_id",
        "category",
        "brand",
        "order_region",
        "customer_region",
        "channel",
        "segment",
        "price",
        "base_price",
        "order_month",
        "order_weekday",
        "is_weekend",
        "lag_1_sales",
        "lag_7_sales",
        "rolling_avg_7",
        "discount_pct",
        "promotion_flag",
        "purchase_frequency",
        "margin_pct",
        "popularity_score",
    ]

    demand_target = "target_demand"

    missing_cols = [
        col for col in demand_features + [demand_target]
        if col not in demand_df.columns
    ]

    if missing_cols:
        raise ValueError(f"Missing columns in demand dataset: {missing_cols}")

    df = demand_df[demand_features + [demand_target]].copy()
    df = df.dropna()

    X = df[demand_features]
    y = df[demand_target]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    model = build_demand_model()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    metrics = {
        "model_type": "regression",
        "rows_total": int(len(df)),
        "rows_train": int(len(X_train)),
        "rows_test": int(len(X_test)),
        "r2_score": float(r2_score(y_test, y_pred)),
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "mse": float(mean_squared_error(y_test, y_pred)),
        "rmse": _rmse(y_test, y_pred),
    }

    return model, metrics


def train_anomaly_model(anomaly_df):
    anomaly_features = [
        "quantity",
        "price",
        "total_amount",
        "unit_price",
        "discount_pct",
        "promotion_flag",
    ]

    anomaly_features = [col for col in anomaly_features if col in anomaly_df.columns]

    missing_cols = [
        col for col in ["quantity", "price", "total_amount", "unit_price"]
        if col not in anomaly_df.columns
    ]

    if missing_cols:
        raise ValueError(f"Missing columns in anomaly dataset: {missing_cols}")

    df = anomaly_df.copy()
    df = df.dropna(subset=anomaly_features)

    X = df[anomaly_features]

    model = build_anomaly_model()
    model.fit(X)

    raw_pred = model.predict(X)
    anomaly_flags = np.where(raw_pred == -1, 1, 0)

    anomaly_count = int(anomaly_flags.sum())
    normal_count = int(len(anomaly_flags) - anomaly_count)
    anomaly_rate = float(anomaly_count / len(anomaly_flags)) if len(anomaly_flags) else 0.0

    metrics = {
        "model_type": "unsupervised_anomaly_detection",
        "rows_total": int(len(df)),
        "normal_count": normal_count,
        "anomaly_count": anomaly_count,
        "anomaly_rate": anomaly_rate,
    }

    label_col = None
    for col in ["anomaly_flag", "is_anomaly", "label", "target"]:
        if col in df.columns:
            label_col = col
            break

    if label_col is not None:
        y_true = pd.to_numeric(df[label_col], errors="coerce").fillna(0).astype(int)
        y_pred = anomaly_flags

        metrics.update(
            {
                "label_column": label_col,
                "accuracy": float(accuracy_score(y_true, y_pred)),
                "precision": float(precision_score(y_true, y_pred, zero_division=0)),
                "recall": float(recall_score(y_true, y_pred, zero_division=0)),
                "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
            }
        )
    else:
        metrics.update(
            {
                "accuracy": None,
                "precision": None,
                "recall": None,
                "f1_score": None,
                "note": "F1/accuracy not calculated because true anomaly labels are not available.",
            }
        )

    return model, metrics


def train_clustering_model(customer_df):
    clustering_features = [
        "customer_total_spend",
        "customer_total_orders",
        "avg_order_value",
        "recency_days",
        "purchase_frequency",
        "age",
        "discount_sensitivity",
    ]

    missing_cols = [
        col for col in clustering_features
        if col not in customer_df.columns
    ]

    if missing_cols:
        raise ValueError(f"Missing columns in customer dataset: {missing_cols}")

    df = customer_df.copy()
    df = df.dropna(subset=clustering_features)

    X = df[clustering_features]

    model = build_clustering_model()
    model.fit(X)

    cluster_labels = model.predict(X)

    unique_clusters, counts = np.unique(cluster_labels, return_counts=True)
    cluster_distribution = {
        str(cluster): int(count)
        for cluster, count in zip(unique_clusters, counts)
    }

    if len(set(cluster_labels)) > 1 and len(X) > len(set(cluster_labels)):
        scaled_x = model.named_steps["scaler"].transform(X)
        silhouette = float(silhouette_score(scaled_x, cluster_labels))
    else:
        silhouette = None

    metrics = {
        "model_type": "clustering",
        "rows_total": int(len(df)),
        "n_clusters": int(len(set(cluster_labels))),
        "cluster_distribution": cluster_distribution,
        "silhouette_score": silhouette,
    }

    customer_segments = customer_df.copy()
    customer_segments["cluster"] = model.predict(
        customer_segments[clustering_features].fillna(0)
    )

    return model, metrics, customer_segments


def train_all_models():
    products, customers, orders = load_raw_data()

    master_df = build_master_table(products, customers, orders)
    demand_df = build_demand_dataset(master_df)
    anomaly_df = build_anomaly_dataset(master_df)
    customer_df = build_customer_dataset(master_df)

    demand_model, demand_metrics = train_demand_model(demand_df)
    anomaly_model, anomaly_metrics = train_anomaly_model(anomaly_df)
    clustering_model, clustering_metrics, customer_segments = train_clustering_model(customer_df)

    demand_model_path = MODEL_DIR / "demand_model.joblib"
    anomaly_model_path = MODEL_DIR / "anomaly_model.joblib"
    clustering_model_path = MODEL_DIR / "clustering_model.joblib"

    joblib.dump(demand_model, demand_model_path)
    joblib.dump(anomaly_model, anomaly_model_path)
    joblib.dump(clustering_model, clustering_model_path)

    master_df.to_csv(CURATED_DIR / "master_sales_dataset.csv", index=False)
    demand_df.to_csv(CURATED_DIR / "demand_dataset.csv", index=False)
    anomaly_df.to_csv(CURATED_DIR / "anomaly_dataset.csv", index=False)
    customer_segments.to_csv(CURATED_DIR / "customer_segments.csv", index=False)

    summary = {
        "trained_at": datetime.utcnow().isoformat(),
        "rows_master": int(len(master_df)),
        "rows_demand": int(len(demand_df)),
        "rows_anomaly": int(len(anomaly_df)),
        "rows_customers": int(len(customer_df)),
        "models_saved": [
            str(demand_model_path),
            str(anomaly_model_path),
            str(clustering_model_path),
        ],
        "curated_files_saved": [
            str(CURATED_DIR / "master_sales_dataset.csv"),
            str(CURATED_DIR / "demand_dataset.csv"),
            str(CURATED_DIR / "anomaly_dataset.csv"),
            str(CURATED_DIR / "customer_segments.csv"),
        ],
        "metrics_file": str(METRICS_DIR / "training_metrics.json"),
        "metrics": {
            "demand_forecasting": demand_metrics,
            "anomaly_detection": anomaly_metrics,
            "customer_clustering": clustering_metrics,
        },
    }

    metrics_path = METRICS_DIR / "training_metrics.json"

    with open(metrics_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    insert_one("training_runs", summary)

    logger.info("Training complete")
    print(json.dumps(summary, indent=4))

    return summary