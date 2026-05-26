from pydantic import BaseModel, Field


class DemandPredictionRequest(BaseModel):
    product_id: str = Field(..., examples=["P001"])
    forecast_date: str = Field(..., examples=["2026-06-01"])


class AnomalyRequest(BaseModel):
    quantity: float = Field(..., gt=0, examples=[20])
    price: float = Field(..., gt=0, examples=[6800])
    discount_pct: float = Field(0, ge=0, examples=[0])
    promotion_flag: int = Field(0, ge=0, le=1, examples=[0])


class SupportQuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, examples=["What is the return policy for P001?"])


class SalesInsightRequest(BaseModel):
    product_id: str = Field(..., examples=["P001"])
    forecast_date: str = Field(..., examples=["2026-06-01"])


class AnalyticsInsightRequest(BaseModel):
    question: str | None = Field(None, examples=["Summarize anomaly trends and customer segments."])