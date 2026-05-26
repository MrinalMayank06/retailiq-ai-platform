from __future__ import annotations

from datetime import datetime

from src.agents.shared.llm_client import get_llm_client
from src.ml.inference.predict import predict_demand
from src.database.crud import insert_one


def generate_sales_insight(product_id: str, forecast_date: str) -> dict:
    forecast = predict_demand(product_id, forecast_date)

    system_prompt = """
You are RetailIQ Sales Agent.
You convert ML demand forecasts into business recommendations.
Your output must be useful for a retail manager.
Focus on inventory, pricing, promotion, risk, and next action.
"""

    user_prompt = f"""
Demand Forecast Output:
{forecast}

Generate:
1. Demand summary
2. Stock recommendation
3. Promotion or pricing recommendation
4. Risk note
5. Final business action
"""

    llm = get_llm_client()

    insight = llm.chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.35,
        max_tokens=800,
    )

    response = {
        "product_id": product_id,
        "forecast_date": forecast_date,
        "forecast": forecast,
        "insight": insight,
        "agent": "sales_agent",
        "created_at": datetime.utcnow().isoformat(),
    }

    try:
        insert_one("chat_logs", response)
    except Exception:
        pass

    return response