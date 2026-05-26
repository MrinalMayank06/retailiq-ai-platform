from fastapi import APIRouter

from src.api.schemas.request_models import (
    SupportQuestionRequest,
    SalesInsightRequest,
    AnalyticsInsightRequest,
)
from src.api.utils.response_formatter import success_response
from src.agents.support_agent.rag_pipeline import answer_support_question
from src.agents.sales_agent.agent import generate_sales_insight
from src.agents.analytics_agent.agent import generate_analytics_insight

router = APIRouter(prefix="/api/agents", tags=["Agents"])


@router.post("/support-chat")
def support_chat(request: SupportQuestionRequest):
    result = answer_support_question(request.question)
    return success_response("Support agent response generated successfully", result)


@router.post("/sales-insight")
def sales_insight(request: SalesInsightRequest):
    result = generate_sales_insight(request.product_id, request.forecast_date)
    return success_response("Sales insight generated successfully", result)


@router.post("/analytics-insight")
def analytics_insight(request: AnalyticsInsightRequest):
    result = generate_analytics_insight(request.question)
    return success_response("Analytics insight generated successfully", result)