from fastapi import APIRouter

from src.api.utils.response_formatter import success_response
from src.agents.analytics_agent.agent import get_dashboard_metrics
from src.database.crud import find_many
from src.database.collections import TRAINING_RUNS

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard-metrics")
def dashboard_metrics():
    result = get_dashboard_metrics()
    return success_response("Dashboard metrics fetched", result)


@router.get("/training-runs")
def training_runs():
    result = find_many(TRAINING_RUNS, limit=10)
    return success_response("Training run history", result)
