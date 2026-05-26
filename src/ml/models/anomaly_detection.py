from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_anomaly_model():
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "model",
                IsolationForest(
                    n_estimators=200,
                    contamination=0.05,
                    max_samples="auto",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )