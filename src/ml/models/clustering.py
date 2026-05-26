from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_clustering_model():
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "model",
                KMeans(
                    n_clusters=3,
                    random_state=42,
                    n_init=20,
                ),
            ),
        ]
    )