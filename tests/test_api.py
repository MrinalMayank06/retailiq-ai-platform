from fastapi.testclient import TestClient

import src.api.main as main_module


client = TestClient(main_module.app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert "Swagger" in body["message"]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert "RetailIQ" in body["data"]["app_name"]
    assert "env" in body["data"]


def test_platform_status_structure():
    response = client.get("/api/status")
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert "data" in body

    data = body["data"]

    assert "raw_files" in data
    assert "curated_files" in data
    assert "model_files" in data
    assert "azure_components" in data
    assert "retrieval_components" in data
    assert "mcp_tools" in data
    assert "dashboard_summary" in data

    azure_components = data["azure_components"]
    retrieval_components = data["retrieval_components"]

    # Azure configuration checks
    assert (
        "azure_chat_configured" in azure_components
        or "azure_foundry_chat_configured" in azure_components
    )
    assert "azure_embedding_configured" in azure_components
    assert "azure_app_service_ready" in azure_components

    # Final RAG retrieval checks
    assert retrieval_components["rag_backend"] == "azure_embedding_local_json_store"
    assert retrieval_components["embedding_model"] == "text-embedding-3-large"
    assert retrieval_components["embedding_deployment"] == "text-embedding-3-large"
    assert retrieval_components["vector_db"] == "local_json_vector_store"

    assert "knowledge_source" in retrieval_components
    assert retrieval_components["knowledge_source"] == "data/raw/product_details.csv"

    assert "store_artifact" in retrieval_components
    assert "product_knowledge_embeddings.json" in retrieval_components["store_artifact"]

    assert "retrieval_ready" in retrieval_components


def test_demand_forecast_success(monkeypatch):
    def mock_predict_demand(product_id: str, forecast_date: str):
        return {
            "product_id": product_id,
            "forecast_date": forecast_date,
            "predicted_demand": 2.75,
            "features_used": {
                "category": "Electronics",
                "brand": "HP",
            },
        }

    def mock_insert_one(collection_name: str, document: dict):
        return None

    monkeypatch.setattr(main_module, "predict_demand", mock_predict_demand)
    monkeypatch.setattr(main_module, "insert_one", mock_insert_one)

    response = client.post(
        "/api/demand-forecast",
        json={
            "product_id": "P001",
            "forecast_date": "2026-06-15",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["data"]["product_id"] == "P001"
    assert body["data"]["forecast_date"] == "2026-06-15"
    assert "predicted_demand" in body["data"]


def test_demand_forecast_validation_error():
    response = client.post(
        "/api/demand-forecast",
        json={
            "product_id": "P001",
        },
    )

    assert response.status_code == 422


def test_anomaly_check_success(monkeypatch):
    def mock_detect_anomaly(quantity, price, discount_pct, promotion_flag):
        return {
            "quantity": quantity,
            "price": price,
            "discount_pct": discount_pct,
            "promotion_flag": promotion_flag,
            "total_amount": quantity * price,
            "unit_price": price,
            "anomaly_flag": False,
            "anomaly_score": -0.215,
        }

    def mock_insert_one(collection_name: str, document: dict):
        return None

    monkeypatch.setattr(main_module, "detect_anomaly", mock_detect_anomaly)
    monkeypatch.setattr(main_module, "insert_one", mock_insert_one)

    response = client.post(
        "/api/anomaly-check",
        json={
            "quantity": 2,
            "price": 1500,
            "discount_pct": 5,
            "promotion_flag": 0,
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["data"]["anomaly_flag"] is False
    assert body["data"]["total_amount"] == 3000


def test_anomaly_check_validation_error():
    response = client.post(
        "/api/anomaly-check",
        json={
            "quantity": -1,
            "price": 1500,
            "discount_pct": 5,
            "promotion_flag": 0,
        },
    )

    assert response.status_code == 422


def test_agent_support_success(monkeypatch):
    def mock_answer_support_question(question: str):
        return {
            "question": question,
            "answer": "P001 has a 7-day return policy.",
            "sources": [
                {
                    "product_id": "P001",
                    "content": "Return Policy: 7-day return available.",
                    "score": 0.92,
                }
            ],
            "retrieval_source": "azure_embedding_local_json_store",
            "retrieval_error": None,
            "agent": "support_agent",
        }

    monkeypatch.setattr(
        main_module,
        "answer_support_question",
        mock_answer_support_question,
    )

    response = client.post(
        "/api/agent",
        json={
            "intent": "support",
            "question": "What is the return policy for P001?",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["data"]["retrieval_source"] == "azure_embedding_local_json_store"
    assert body["data"]["retrieval_error"] is None
    assert "return policy" in body["data"]["question"].lower()
    assert len(body["data"]["sources"]) > 0


def test_agent_support_missing_question():
    response = client.post(
        "/api/agent",
        json={
            "intent": "support",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "question is required for support intent"


def test_agent_sales_success(monkeypatch):
    def mock_generate_sales_insight(product_id: str, forecast_date: str):
        return {
            "product_id": product_id,
            "forecast_date": forecast_date,
            "forecast": {
                "predicted_demand": 3.4,
            },
            "insight": "Increase stock slightly and monitor pricing.",
            "agent": "sales_agent",
        }

    monkeypatch.setattr(
        main_module,
        "generate_sales_insight",
        mock_generate_sales_insight,
    )

    response = client.post(
        "/api/agent",
        json={
            "intent": "sales",
            "product_id": "P010",
            "forecast_date": "2026-07-01",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["data"]["agent"] == "sales_agent"
    assert body["data"]["product_id"] == "P010"


def test_agent_sales_missing_fields():
    response = client.post(
        "/api/agent",
        json={
            "intent": "sales",
            "product_id": "P010",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "product_id and forecast_date are required for sales intent"


def test_agent_analytics_success(monkeypatch):
    def mock_generate_analytics_insight(question: str | None):
        return {
            "question": question,
            "metrics": {
                "total_orders": 5000,
                "total_revenue": 73636949.19,
            },
            "insight": "Revenue is strong, but anomaly monitoring should continue.",
            "agent": "analytics_agent",
        }

    monkeypatch.setattr(
        main_module,
        "generate_analytics_insight",
        mock_generate_analytics_insight,
    )

    response = client.post(
        "/api/agent",
        json={
            "intent": "analytics",
            "question": "Summarize overall retail performance.",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["data"]["agent"] == "analytics_agent"
    assert "metrics" in body["data"]


def test_agent_invalid_intent_validation():
    response = client.post(
        "/api/agent",
        json={
            "intent": "unknown",
            "question": "test",
        },
    )

    assert response.status_code == 422


def test_logs_when_db_unavailable(monkeypatch):
    def mock_get_db():
        return None

    monkeypatch.setattr(main_module, "get_db", mock_get_db)

    response = client.get("/api/logs")
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["data"]["chat_logs"] == []
    assert body["data"]["prediction_logs"] == []
    assert body["data"]["training_logs"] == []


class _FakeCursor:
    def __init__(self, data):
        self.data = data

    def sort(self, *args, **kwargs):
        return self

    def limit(self, n):
        return self.data[:n]


class _FakeCollection:
    def __init__(self, data):
        self.data = data

    def find(self, *args, **kwargs):
        return _FakeCursor(self.data)


class _FakeDB:
    def __init__(self):
        self.storage = {
            "chat_logs": [
                {"question": "What is the return policy for P001?"},
            ],
            "predictions": [
                {"type": "demo_demand_forecast", "product_id": "P001"},
            ],
            "training_runs": [
                {"trained_at": "2026-05-25T10:00:00"},
            ],
        }

    def __getitem__(self, item):
        return _FakeCollection(self.storage[item])


def test_logs_with_mock_db(monkeypatch):
    def mock_get_db():
        return _FakeDB()

    monkeypatch.setattr(main_module, "get_db", mock_get_db)

    response = client.get("/api/logs?limit=5")
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert len(body["data"]["chat_logs"]) == 1
    assert len(body["data"]["prediction_logs"]) == 1
    assert len(body["data"]["training_logs"]) == 1