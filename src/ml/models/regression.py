from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer


def build_demand_model():
    categorical_features = [
        "product_id",
        "category",
        "brand",
        "order_region",
        "customer_region",
        "channel",
        "segment",
    ]

    numeric_features = [
        "price",
        "base_price",
        "order_month",
        "order_weekday",
        "is_weekend",
        "lag_1_sales",
        "lag_7_sales",
        "rolling_avg_7",
        "discount_pct",
        "promotion_flag",
        "purchase_frequency",
        "margin_pct",
        "popularity_score",
    ]

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", categorical_pipeline, categorical_features),
            ("num", numeric_pipeline, numeric_features),
        ]
    )

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=16,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )