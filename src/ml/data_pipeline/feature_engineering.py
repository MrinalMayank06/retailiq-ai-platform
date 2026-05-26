from __future__ import annotations

import pandas as pd
import numpy as np


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    return df


def _find_column(columns, keywords):
    for col in columns:
        if all(keyword in col for keyword in keywords):
            return col
    return None


def _ensure_column(df: pd.DataFrame, column: str, default):
    if column not in df.columns:
        df[column] = default
    return df


def build_master_table(products: pd.DataFrame, customers: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    products = _normalize_columns(products)
    customers = _normalize_columns(customers)
    orders = _normalize_columns(orders)

    product_id_col = _find_column(products.columns, ["product", "id"])
    customer_id_col = _find_column(customers.columns, ["customer", "id"])
    order_id_col = _find_column(orders.columns, ["order", "id"])
    order_product_id_col = _find_column(orders.columns, ["product", "id"])
    order_customer_id_col = _find_column(orders.columns, ["customer", "id"])

    if product_id_col is None:
        raise ValueError("product_id column not found in products")
    if customer_id_col is None:
        raise ValueError("customer_id column not found in customers")
    if order_id_col is None:
        raise ValueError("order_id column not found in orders")
    if order_product_id_col is None:
        raise ValueError("product_id column not found in orders")
    if order_customer_id_col is None:
        raise ValueError("customer_id column not found in orders")

    products.rename(columns={product_id_col: "product_id"}, inplace=True)
    customers.rename(columns={customer_id_col: "customer_id"}, inplace=True)
    orders.rename(
        columns={
            order_id_col: "order_id",
            order_product_id_col: "product_id",
            order_customer_id_col: "customer_id",
        },
        inplace=True,
    )

    if "quantity" not in orders.columns:
        quantity_col = next((c for c in orders.columns if "qty" in c or "quantity" in c), None)
        if quantity_col is None:
            raise ValueError("quantity column not found in orders")
        orders.rename(columns={quantity_col: "quantity"}, inplace=True)

    if "price" not in orders.columns:
        price_col = next((c for c in orders.columns if "price" in c), None)
        if price_col is None:
            raise ValueError("price column not found in orders")
        orders.rename(columns={price_col: "price"}, inplace=True)

    if "order_date" in orders.columns:
        orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    elif "date" in orders.columns:
        orders["order_date"] = pd.to_datetime(orders["date"], errors="coerce")
    else:
        date_col = next((c for c in orders.columns if "date" in c), None)
        if date_col is None:
            raise ValueError("date column not found in orders")
        orders["order_date"] = pd.to_datetime(orders[date_col], errors="coerce")

    products = _ensure_column(products, "category", "general")
    products = _ensure_column(products, "brand", "generic")
    products = _ensure_column(products, "product_name", products["product_id"].astype(str))
    products = _ensure_column(products, "base_price", 0)
    products = _ensure_column(products, "margin_pct", 0)
    products = _ensure_column(products, "popularity_score", 0)

    customers = _ensure_column(customers, "region", customers["location"] if "location" in customers.columns else "unknown")
    customers = _ensure_column(customers, "segment", "general")
    customers = _ensure_column(customers, "purchase_frequency", 0)
    customers = _ensure_column(customers, "age", 0)
    customers = _ensure_column(customers, "discount_sensitivity", 0)
    customers = _ensure_column(customers, "preferred_channel", "unknown")

    orders = _ensure_column(orders, "discount_pct", 0)
    orders = _ensure_column(orders, "promotion_flag", 0)
    orders = _ensure_column(orders, "channel", "unknown")
    orders = _ensure_column(orders, "payment_method", "unknown")
    orders = _ensure_column(orders, "shipping_status", "unknown")
    orders = _ensure_column(orders, "region", "unknown")
    orders = _ensure_column(orders, "anomaly_flag", np.nan)

    products = products.loc[:, ~products.columns.duplicated()].copy()
    customers = customers.loc[:, ~customers.columns.duplicated()].copy()
    orders = orders.loc[:, ~orders.columns.duplicated()].copy()

    merged = pd.merge(
        orders,
        products,
        on="product_id",
        how="left",
        suffixes=("_order", "_product"),
    )

    merged = pd.merge(
        merged,
        customers,
        on="customer_id",
        how="left",
        suffixes=("", "_customer"),
    )

    merged = merged.loc[:, ~merged.columns.duplicated()].copy()

    if "price_order" in merged.columns:
        merged["price"] = merged["price_order"]
    elif "price" not in merged.columns:
        raise ValueError("price column missing after merge")

    if "base_price_product" in merged.columns:
        merged["base_price"] = merged["base_price_product"]
    elif "base_price" not in merged.columns:
        merged["base_price"] = merged["price"]

    if "category_product" in merged.columns:
        merged["category"] = merged["category_product"]
    elif "category" not in merged.columns:
        merged["category"] = "general"

    if "brand_product" in merged.columns:
        merged["brand"] = merged["brand_product"]
    elif "brand" not in merged.columns:
        merged["brand"] = "generic"

    if "margin_pct_product" in merged.columns:
        merged["margin_pct"] = merged["margin_pct_product"]
    elif "margin_pct" not in merged.columns:
        merged["margin_pct"] = 0

    if "popularity_score_product" in merged.columns:
        merged["popularity_score"] = merged["popularity_score_product"]
    elif "popularity_score" not in merged.columns:
        merged["popularity_score"] = 0

    if "region_customer" in merged.columns:
        merged["customer_region"] = merged["region_customer"]
    elif "location" in merged.columns:
        merged["customer_region"] = merged["location"]
    else:
        merged["customer_region"] = "unknown"

    if "region" in merged.columns:
        merged["order_region"] = merged["region"]
    else:
        merged["order_region"] = "unknown"

    if "segment_customer" in merged.columns:
        merged["segment"] = merged["segment_customer"]
    elif "segment" not in merged.columns:
        merged["segment"] = "general"

    merged["order_date"] = pd.to_datetime(merged["order_date"].astype(str), errors="coerce")
    merged["price"] = pd.to_numeric(merged["price"], errors="coerce").fillna(0.0)
    merged["base_price"] = pd.to_numeric(merged["base_price"], errors="coerce").fillna(merged["price"])
    merged["quantity"] = pd.to_numeric(merged["quantity"], errors="coerce").fillna(0)
    merged["discount_pct"] = pd.to_numeric(merged["discount_pct"], errors="coerce").fillna(0)
    merged["promotion_flag"] = pd.to_numeric(merged["promotion_flag"], errors="coerce").fillna(0).astype(int)
    merged["purchase_frequency"] = pd.to_numeric(merged["purchase_frequency"], errors="coerce").fillna(0)
    merged["age"] = pd.to_numeric(merged["age"], errors="coerce").fillna(0)
    merged["discount_sensitivity"] = pd.to_numeric(merged["discount_sensitivity"], errors="coerce").fillna(0)
    merged["margin_pct"] = pd.to_numeric(merged["margin_pct"], errors="coerce").fillna(0)
    merged["popularity_score"] = pd.to_numeric(merged["popularity_score"], errors="coerce").fillna(0)

    merged["category"] = merged["category"].fillna("general").astype(str)
    merged["brand"] = merged["brand"].fillna("generic").astype(str)
    merged["segment"] = merged["segment"].fillna("general").astype(str)
    merged["customer_region"] = merged["customer_region"].fillna("unknown").astype(str)
    merged["order_region"] = merged["order_region"].fillna("unknown").astype(str)
    merged["channel"] = merged["channel"].fillna("unknown").astype(str)
    merged["payment_method"] = merged["payment_method"].fillna("unknown").astype(str)
    merged["shipping_status"] = merged["shipping_status"].fillna("unknown").astype(str)

    if "total_amount" not in merged.columns:
        merged["total_amount"] = merged["quantity"] * merged["price"]
    else:
        merged["total_amount"] = pd.to_numeric(merged["total_amount"], errors="coerce")
        merged["total_amount"] = merged["total_amount"].fillna(merged["quantity"] * merged["price"])

    merged["order_day"] = merged["order_date"].dt.day.fillna(0).astype(int)
    merged["order_month"] = merged["order_date"].dt.month.fillna(0).astype(int)
    merged["order_weekday"] = merged["order_date"].dt.weekday.fillna(0).astype(int)
    merged["is_weekend"] = merged["order_weekday"].isin([5, 6]).astype(int)
    merged["year"] = merged["order_date"].dt.year.fillna(0).astype(int)
    merged["month_period"] = merged["order_date"].dt.to_period("M").astype(str)

    return merged


def build_demand_dataset(master_df: pd.DataFrame) -> pd.DataFrame:
    df = master_df.copy()

    required_defaults = {
        "category": "general",
        "brand": "generic",
        "order_region": "unknown",
        "customer_region": "unknown",
        "channel": "unknown",
        "segment": "general",
        "discount_pct": 0,
        "promotion_flag": 0,
        "purchase_frequency": 0,
        "base_price": 0,
        "margin_pct": 0,
        "popularity_score": 0,
    }

    for column, default in required_defaults.items():
        if column not in df.columns:
            df[column] = default

    daily = (
        df.groupby(["product_id", "order_date"], as_index=False)
        .agg(
            quantity=("quantity", "sum"),
            total_amount=("total_amount", "sum"),
            price=("price", "mean"),
            base_price=("base_price", "mean"),
            category=("category", "first"),
            brand=("brand", "first"),
            order_region=("order_region", "first"),
            customer_region=("customer_region", "first"),
            channel=("channel", "first"),
            segment=("segment", "first"),
            discount_pct=("discount_pct", "mean"),
            promotion_flag=("promotion_flag", "max"),
            purchase_frequency=("purchase_frequency", "mean"),
            margin_pct=("margin_pct", "mean"),
            popularity_score=("popularity_score", "mean"),
        )
        .sort_values(["product_id", "order_date"])
    )

    text_cols = ["category", "brand", "order_region", "customer_region", "channel", "segment"]
    for col in text_cols:
        daily[col] = daily[col].fillna("unknown").astype(str)

    numeric_cols = [
        "price",
        "base_price",
        "discount_pct",
        "promotion_flag",
        "purchase_frequency",
        "margin_pct",
        "popularity_score",
    ]
    for col in numeric_cols:
        daily[col] = pd.to_numeric(daily[col], errors="coerce").fillna(0)

    daily["order_month"] = daily["order_date"].dt.month.fillna(0).astype(int)
    daily["order_weekday"] = daily["order_date"].dt.weekday.fillna(0).astype(int)
    daily["is_weekend"] = daily["order_weekday"].isin([5, 6]).astype(int)

    daily["lag_1_sales"] = daily.groupby("product_id")["quantity"].shift(1)
    daily["lag_7_sales"] = daily.groupby("product_id")["quantity"].shift(7)

    daily["rolling_avg_7"] = (
        daily.groupby("product_id")["quantity"]
        .transform(lambda x: x.rolling(window=7, min_periods=1).mean())
    )

    daily["lag_1_sales"] = daily["lag_1_sales"].fillna(0)
    daily["lag_7_sales"] = daily["lag_7_sales"].fillna(0)
    daily["rolling_avg_7"] = daily["rolling_avg_7"].fillna(0)
    daily["target_demand"] = daily["quantity"]

    return daily


def build_anomaly_dataset(master_df: pd.DataFrame) -> pd.DataFrame:
    df = master_df.copy()

    df["unit_price"] = np.where(
        df["quantity"] > 0,
        df["total_amount"] / df["quantity"],
        0.0,
    )

    columns = [
        "order_id",
        "product_id",
        "customer_id",
        "quantity",
        "price",
        "total_amount",
        "unit_price",
        "discount_pct",
        "promotion_flag",
    ]

    if "anomaly_flag" in df.columns:
        columns.append("anomaly_flag")

    available_columns = [col for col in columns if col in df.columns]

    return df[available_columns].copy()


def build_customer_dataset(master_df: pd.DataFrame) -> pd.DataFrame:
    df = master_df.copy()

    for col in ["purchase_frequency", "age", "discount_sensitivity"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    latest_date = df["order_date"].max()

    customer_df = (
        df.groupby("customer_id", as_index=False)
        .agg(
            customer_total_spend=("total_amount", "sum"),
            customer_total_orders=("order_id", "nunique"),
            avg_order_value=("total_amount", "mean"),
            last_order_date=("order_date", "max"),
            purchase_frequency=("purchase_frequency", "mean"),
            age=("age", "mean"),
            discount_sensitivity=("discount_sensitivity", "mean"),
        )
    )

    customer_df["recency_days"] = (
        latest_date - customer_df["last_order_date"]
    ).dt.days.fillna(0)

    return customer_df