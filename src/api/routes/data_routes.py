from fastapi import APIRouter
import pandas as pd

from src.common.constants import DATA_RAW_DIR, DATA_CURATED_DIR
from src.api.utils.response_formatter import success_response

router = APIRouter(prefix="/api/data", tags=["Data"])


@router.get("/status")
def data_status():
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

    return success_response(
        "Data file status",
        {
            "raw": raw_files,
            "curated": curated_files,
        },
    )


@router.get("/preview/master")
def preview_master(limit: int = 5):
    path = DATA_CURATED_DIR / "master_sales_dataset.csv"

    if not path.exists():
        return success_response("Curated data not available yet", [])

    df = pd.read_csv(path)
    return success_response("Master sales dataset preview", df.head(limit).to_dict(orient="records"))