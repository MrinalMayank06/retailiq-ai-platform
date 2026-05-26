from fastapi import APIRouter

from src.api.schemas.request_models import DemandPredictionRequest, AnomalyRequest
from src.api.utils.response_formatter import success_response
from src.database.crud import insert_one
from src.database.collections import PREDICTIONS
from src.ml.training.train_model import train_all_models
from src.ml.inference.predict import predict_demand, detect_anomaly, segment_customers

router = APIRouter(prefix="/api/ml", tags=["ML"])


@router.post("/train")
def train_models():
    result = train_all_models()
    return success_response("Models trained successfully", result)


@router.post("/predict-demand")
def predict_demand_route(request: DemandPredictionRequest):
    result = predict_demand(request.product_id, request.forecast_date)
    insert_one(PREDICTIONS, {"type": "demand_prediction", **result})
    return success_response("Demand predicted successfully", result)


@router.post("/detect-anomaly")
def detect_anomaly_route(request: AnomalyRequest):
    result = detect_anomaly(
        request.quantity,
        request.price,
        request.discount_pct,
        request.promotion_flag,
    )
    insert_one(PREDICTIONS, {"type": "anomaly_prediction", **result})
    return success_response("Anomaly scored successfully", result)


@router.get("/segment-customers")
def segment_customers_route():
    result = segment_customers()
    return success_response("Customer segments generated", result)