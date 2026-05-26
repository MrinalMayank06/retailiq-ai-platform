from fastapi import APIRouter

from src.database.mongo_client import get_db
from src.api.utils.response_formatter import success_response

router = APIRouter(prefix="/api/logs", tags=["Logs"])


@router.get("/chat")
def get_chat_logs(limit: int = 10):
    db = get_db()
    logs = list(
        db["chat_logs"]
        .find({}, {"_id": 0})
        .sort("created_at", -1)
        .limit(limit)
    )

    return success_response("Chat logs fetched successfully", logs)


@router.get("/predictions")
def get_prediction_logs(limit: int = 10):
    db = get_db()
    logs = list(
        db["predictions"]
        .find({}, {"_id": 0})
        .limit(limit)
    )

    return success_response("Prediction logs fetched successfully", logs)


@router.get("/training")
def get_training_logs(limit: int = 5):
    db = get_db()
    logs = list(
        db["training_runs"]
        .find({}, {"_id": 0})
        .limit(limit)
    )

    return success_response("Training logs fetched successfully", logs)