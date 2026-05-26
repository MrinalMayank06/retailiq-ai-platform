import pandas as pd


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [
        str(col).strip().lower().replace(" ", "_").replace("-", "_")
        for col in out.columns
    ]
    return out


def normalize_inputs(products: pd.DataFrame, customers: pd.DataFrame, orders: pd.DataFrame):
    products = _normalize_columns(products)
    customers = _normalize_columns(customers)
    orders = _normalize_columns(orders)

    # common fallbacks
    if "unit_price" in products.columns and "price" not in products.columns:
        products["price"] = products["unit_price"]
    if "customerid" in customers.columns and "customer_id" not in customers.columns:
        customers["customer_id"] = customers["customerid"]
    if "productid" in products.columns and "product_id" not in products.columns:
        products["product_id"] = products["productid"]
    if "productid" in orders.columns and "product_id" not in orders.columns:
        orders["product_id"] = orders["productid"]
    if "customerid" in orders.columns and "customer_id" not in orders.columns:
        orders["customer_id"] = orders["customerid"]
    if "orderdate" in orders.columns and "order_date" not in orders.columns:
        orders["order_date"] = orders["orderdate"]
    if "date" in orders.columns and "order_date" not in orders.columns:
        orders["order_date"] = orders["date"]

    return products, customers, orders


def clean_products(products: pd.DataFrame) -> pd.DataFrame:
    df = products.copy()
    if "price" not in df.columns:
        df["price"] = 0.0
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    for col in ["product_id", "category", "brand", "product_name"]:
        if col not in df.columns:
            df[col] = "unknown"
        df[col] = df[col].fillna("unknown").astype(str)
    return df.drop_duplicates(subset=["product_id"])


def clean_customers(customers: pd.DataFrame) -> pd.DataFrame:
    df = customers.copy()
    for col in ["customer_id", "region", "segment"]:
        if col not in df.columns:
            df[col] = "unknown"
        df[col] = df[col].fillna("unknown").astype(str)
    return df.drop_duplicates(subset=["customer_id"])


def clean_orders(orders: pd.DataFrame) -> pd.DataFrame:
    df = orders.copy()
    for col in ["order_id", "customer_id", "product_id"]:
        if col not in df.columns:
            df[col] = "unknown"
        df[col] = df[col].fillna("unknown").astype(str)

    if "quantity" not in df.columns:
        df["quantity"] = 1
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1)
    df = df[df["quantity"] > 0]

    if "order_date" not in df.columns:
        raise ValueError("order_data.csv must have order_date/date/Order Date column")
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df = df.dropna(subset=["order_date"])

    return df.drop_duplicates(subset=["order_id"])


def preprocess_all(products: pd.DataFrame, customers: pd.DataFrame, orders: pd.DataFrame):
    products, customers, orders = normalize_inputs(products, customers, orders)
    products = clean_products(products)
    customers = clean_customers(customers)
    orders = clean_orders(orders)
    return products, customers, orders
