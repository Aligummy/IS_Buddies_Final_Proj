"""
Knowledge Analysis & Prediction module.
Implements Simple Linear Regression (SLR) and Random Forest for:
  - Product Demand Prediction
  - Sales Prediction
  - Slow-Moving Product Classification
  - Best-Selling Product Classification

Models can be trained, saved (pickle), loaded, and used for prediction.
"""
import os
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    f1_score,
)
from sklearn.model_selection import train_test_split

# Directory where trained models are persisted
MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
DATASET_DIR = os.path.join(os.path.dirname(__file__), "datasets")
os.makedirs(MODEL_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _model_path(prediction_type: str, model_name: str) -> str:
    return os.path.join(MODEL_DIR, f"{prediction_type}_{model_name}.pkl")


def _save_model(model, prediction_type: str, model_name: str):
    path = _model_path(prediction_type, model_name)
    with open(path, "wb") as f:
        pickle.dump(model, f)
    return path


def _load_model(prediction_type: str, model_name: str):
    path = _model_path(prediction_type, model_name)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def _load_dataset(name: str) -> pd.DataFrame:
    path = os.path.join(DATASET_DIR, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found: {path}")
    return pd.read_csv(path)


# Metric description lookup for evaluation metrics
METRIC_DESCRIPTIONS = {
    "MAE": "Mean Absolute Error – average of absolute differences between predicted and actual values. Lower is better.",
    "MSE": "Mean Squared Error – average of squared differences. Penalises larger errors more. Lower is better.",
    "RMSE": "Root Mean Squared Error – square root of MSE, in the same units as the target. Lower is better.",
    "R2": "R-squared (Coefficient of Determination) – proportion of variance explained by the model. Closer to 1.0 is better.",
    "Accuracy": "Percentage of correct predictions out of total predictions. Higher is better.",
    "Precision": "Of all positive predictions, how many were actually positive. Higher is better.",
    "Recall": "Of all actual positives, how many were correctly predicted. Higher is better.",
    "F1 Score": "Harmonic mean of Precision and Recall. Balances both metrics. Higher is better.",
}


# ---------------------------------------------------------------------------
# 1. Product Demand Prediction
# ---------------------------------------------------------------------------

DOW_MAP = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6
}

def train_demand(model_name: str = "slr"):
    """Train product demand prediction model and return metrics."""
    df = _load_dataset("product_demand.csv")

    df["day_of_week"] = df["day_of_week"].astype(str).str.strip().map(DOW_MAP).fillna(0)

    features = ["month", "day_of_week", "is_school_season", "unit_price", "stock_level"]
    X = df[features].values.astype(float)
    y = df["qty_sold"].values.astype(float)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    if model_name == "slr":
        model = LinearRegression()
    else:
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    metrics = {
        "MAE": round(float(mean_absolute_error(y_test, y_pred)), 4),
        "MSE": round(float(mean_squared_error(y_test, y_pred)), 4),
        "RMSE": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
        "R2": round(float(r2_score(y_test, y_pred)), 4),
    }

    _save_model(model, "demand", model_name)
    return metrics


def predict_demand(model_name: str, month: int, day_of_week: int,
                   is_school_season: int, unit_price: float, stock_level: int):
    """Predict demand qty for given inputs."""
    model = _load_model("demand", model_name)
    if model is None:
        raise ValueError(f"No saved {model_name} model for demand. Train first.")
    X = np.array([[month, day_of_week, is_school_season, unit_price, stock_level]])
    pred = model.predict(X)[0]
    return round(float(pred), 2)


# ---------------------------------------------------------------------------
# 2. Sales Prediction (monthly revenue forecasting)
# ---------------------------------------------------------------------------

def train_sales(model_name: str = "slr"):
    """Train sales prediction model and return metrics."""
    df = _load_dataset("sales_history.csv")

    features = ["month", "year", "qty_sold", "unit_price", "discount_pct"]
    X = df[features].values
    y = df["net_amount"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    if model_name == "slr":
        model = LinearRegression()
    else:
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    metrics = {
        "MAE": round(float(mean_absolute_error(y_test, y_pred)), 4),
        "MSE": round(float(mean_squared_error(y_test, y_pred)), 4),
        "RMSE": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
        "R2": round(float(r2_score(y_test, y_pred)), 4),
    }

    _save_model(model, "sales", model_name)
    return metrics


def predict_sales(model_name: str, month: int, year: int,
                  qty_sold: int, unit_price: float, discount_pct: float):
    """Predict net sales amount."""
    model = _load_model("sales", model_name)
    if model is None:
        raise ValueError(f"No saved {model_name} model for sales. Train first.")
    X = np.array([[month, year, qty_sold, unit_price, discount_pct]])
    pred = model.predict(X)[0]
    return round(float(pred), 2)


# ---------------------------------------------------------------------------
# 3. Slow-Moving Product Classification
# ---------------------------------------------------------------------------

def train_slow_moving(model_name: str = "slr"):
    """Train slow-moving product classifier and return metrics."""
    df = _load_dataset("slow_moving_products.csv")

    features = ["unit_price", "avg_monthly_sales", "stock_level",
                 "days_since_last_sale", "reorder_level", "turnover_rate"]
    X = df[features].values
    y = df["is_slow_moving"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    if model_name == "slr":
        # Use logistic-like approach: linear regression then threshold
        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred_raw = model.predict(X_test)
        y_pred = (y_pred_raw >= 0.5).astype(int)
    else:
        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

    metrics = {
        "Accuracy": round(accuracy_score(y_test, y_pred) * 100, 2),
        "Precision": round(precision_score(y_test, y_pred, zero_division=0) * 100, 2),
        "Recall": round(recall_score(y_test, y_pred, zero_division=0) * 100, 2),
        "F1 Score": round(f1_score(y_test, y_pred, zero_division=0) * 100, 2),
    }

    _save_model(model, "slow_moving", model_name)
    return metrics


def predict_slow_moving(model_name: str, unit_price: float, avg_monthly_sales: float,
                        stock_level: int, days_since_last_sale: int,
                        reorder_level: int, turnover_rate: float):
    """Predict whether a product is slow-moving (1) or not (0)."""
    model = _load_model("slow_moving", model_name)
    if model is None:
        raise ValueError(f"No saved {model_name} model for slow_moving. Train first.")
    X = np.array([[unit_price, avg_monthly_sales, stock_level,
                   days_since_last_sale, reorder_level, turnover_rate]])
    if model_name == "slr":
        pred = model.predict(X)[0]
        return 1 if pred >= 0.5 else 0
    return int(model.predict(X)[0])


# ---------------------------------------------------------------------------
# 4. Best-Selling Product Classification
# ---------------------------------------------------------------------------

def train_best_selling(model_name: str = "slr"):
    """Train best-selling product classifier and return metrics."""
    df = _load_dataset("best_selling_products.csv")

    features = ["unit_price", "total_qty_sold", "total_revenue",
                 "avg_monthly_sales", "months_available", "popularity_score"]
    X = df[features].values
    y = df["is_best_seller"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    if model_name == "slr":
        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred_raw = model.predict(X_test)
        y_pred = (y_pred_raw >= 0.5).astype(int)
    else:
        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

    metrics = {
        "Accuracy": round(accuracy_score(y_test, y_pred) * 100, 2),
        "Precision": round(precision_score(y_test, y_pred, zero_division=0) * 100, 2),
        "Recall": round(recall_score(y_test, y_pred, zero_division=0) * 100, 2),
        "F1 Score": round(f1_score(y_test, y_pred, zero_division=0) * 100, 2),
    }

    _save_model(model, "best_selling", model_name)
    return metrics


def predict_best_selling(model_name: str, unit_price: float, total_qty_sold: int,
                         total_revenue: float, avg_monthly_sales: float,
                         months_available: int, popularity_score: float):
    """Predict whether a product is best-selling (1) or not (0)."""
    model = _load_model("best_selling", model_name)
    if model is None:
        raise ValueError(f"No saved {model_name} model for best_selling. Train first.")
    X = np.array([[unit_price, total_qty_sold, total_revenue,
                   avg_monthly_sales, months_available, popularity_score]])
    if model_name == "slr":
        pred = model.predict(X)[0]
        return 1 if pred >= 0.5 else 0
    return int(model.predict(X)[0])


# ---------------------------------------------------------------------------
# Dataset preview helpers
# ---------------------------------------------------------------------------

def get_dataset_preview(dataset_name: str, rows: int = 20) -> dict:
    """Return first N rows and stats of a dataset."""
    df = _load_dataset(dataset_name)
    return {
        "columns": list(df.columns),
        "rows": df.head(rows).values.tolist(),
        "total_rows": len(df),
        "dtypes": {col: str(dt) for col, dt in df.dtypes.items()},
    }


def get_dataset_info() -> list:
    """List available datasets with row counts."""
    info = []
    for fname in sorted(os.listdir(DATASET_DIR)):
        if fname.endswith(".csv"):
            df = pd.read_csv(os.path.join(DATASET_DIR, fname))
            info.append({"name": fname, "rows": len(df), "columns": len(df.columns)})
    return info
