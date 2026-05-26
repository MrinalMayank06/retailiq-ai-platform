from __future__ import annotations

import joblib
import pandas as pd

from src.common.constants import MODELS_DIR, DATA_CURATED_DIR
from src.common.exceptions import ModelNotFoundError


def _load_model(filename: str):
    path = MODELS_DIR / filename
    if not path.exists():
        raise ModelNotFoundError(f"Model not found: {path}")
    return joblib.load(path)


def _safe_value(row, column, default):
    if column in row.index and pd.notna(row[column]):
        return row[column]
    return default


def predict_demand(product_id: str, forecast_date: str) -> dict:
    model = _load_model("demand_model.joblib")

    demand_df_path = DATA_CURATED_DIR / "demand_dataset.csv"
    if not demand_df_path.exists():
        raise ModelNotFoundError("Curated demand dataset missing. Run training first.")

    df = pd.read_csv(demand_df_path)
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

    product_rows = df[df["product_id"].astype(str) == str(product_id)].sort_values("order_date")

    if product_rows.empty:
        raise ValueError(f"Unknown product_id: {product_id}")

    latest = product_rows.iloc[-1].copy()
    dt = pd.to_datetime(forecast_date)

    feature_row = {
        "product_id": str(_safe_value(latest, "product_id", product_id)),
        "category": str(_safe_value(latest, "category", "general")),
        "brand": str(_safe_value(latest, "brand", "generic")),
        "order_region": str(_safe_value(latest, "order_region", "unknown")),
        "customer_region": str(_safe_value(latest, "customer_region", "unknown")),
        "channel": str(_safe_value(latest, "channel", "unknown")),
        "segment": str(_safe_value(latest, "segment", "general")),
        "price": float(_safe_value(latest, "price", 0)),
        "base_price": float(_safe_value(latest, "base_price", _safe_value(latest, "price", 0))),
        "order_month": int(dt.month),
        "order_weekday": int(dt.weekday()),
        "is_weekend": int(dt.weekday() in [5, 6]),
        "lag_1_sales": float(_safe_value(latest, "quantity", 0)),
        "lag_7_sales": float(_safe_value(latest, "lag_7_sales", _safe_value(latest, "quantity", 0))),
        "rolling_avg_7": float(_safe_value(latest, "rolling_avg_7", _safe_value(latest, "quantity", 0))),
        "discount_pct": float(_safe_value(latest, "discount_pct", 0)),
        "promotion_flag": int(_safe_value(latest, "promotion_flag", 0)),
        "purchase_frequency": float(_safe_value(latest, "purchase_frequency", 0)),
        "margin_pct": float(_safe_value(latest, "margin_pct", 0)),
        "popularity_score": float(_safe_value(latest, "popularity_score", 0)),
    }

    features_df = pd.DataFrame([feature_row])
    prediction = model.predict(features_df)[0]

    return {
        "product_id": str(product_id),
        "forecast_date": str(dt.date()),
        "predicted_demand": round(float(prediction), 2),
        "features_used": feature_row,
    }


def detect_anomaly(
    quantity: float,
    price: float,
    discount_pct: float = 0,
    promotion_flag: int = 0,
) -> dict:
    model = _load_model("anomaly_model.joblib")

    total_amount = float(quantity) * float(price)
    unit_price = float(total_amount / quantity) if quantity else 0.0

    features_df = pd.DataFrame(
        [
            {
                "quantity": float(quantity),
                "price": float(price),
                "total_amount": float(total_amount),
                "unit_price": float(unit_price),
                "discount_pct": float(discount_pct),
                "promotion_flag": int(promotion_flag),
            }
        ]
    )

    prediction = model.predict(features_df)[0]
    score = model.score_samples(features_df)[0]

    return {
        "quantity": float(quantity),
        "price": float(price),
        "discount_pct": float(discount_pct),
        "promotion_flag": int(promotion_flag),
        "total_amount": round(total_amount, 2),
        "unit_price": round(unit_price, 2),
        "anomaly_flag": bool(prediction == -1),
        "anomaly_score": round(float(score), 4),
    }


def segment_customers() -> list[dict]:
    model = _load_model("clustering_model.joblib")

    customer_df_path = DATA_CURATED_DIR / "customer_segments.csv"
    if not customer_df_path.exists():
        raise ModelNotFoundError("Curated customer dataset missing. Run training first.")

    df = pd.read_csv(customer_df_path)

    features = [
        "customer_total_spend",
        "customer_total_orders",
        "avg_order_value",
        "recency_days",
        "purchase_frequency",
        "age",
        "discount_sensitivity",
    ]

    missing = [col for col in features if col not in df.columns]
    if missing:
        raise ValueError(f"Missing customer segment features: {missing}")

    df["cluster"] = model.predict(df[features].fillna(0))

    return df[
        [
            "customer_id",
            "customer_total_spend",
            "customer_total_orders",
            "avg_order_value",
            "recency_days",
            "purchase_frequency",
            "age",
            "discount_sensitivity",
            "cluster",
        ]
    ].to_dict(orient="records")