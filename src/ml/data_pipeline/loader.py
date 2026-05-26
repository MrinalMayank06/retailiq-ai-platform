from pathlib import Path
import pandas as pd

from src.common.constants import DATA_RAW_DIR
from src.common.exceptions import DataValidationError


REQUIRED_FILES = {
    "products": "product_details.csv",
    "customers": "customer_data.csv",
    "orders": "order_data.csv",
}


def load_csv(filename: str) -> pd.DataFrame:
    path = DATA_RAW_DIR / filename
    if not path.exists():
        raise DataValidationError(f"Missing file: {path}")
    return pd.read_csv(path)


def load_raw_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    products = load_csv(REQUIRED_FILES["products"])
    customers = load_csv(REQUIRED_FILES["customers"])
    orders = load_csv(REQUIRED_FILES["orders"])
    return products, customers, orders
