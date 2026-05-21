import os
import pickle
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline

from .ml_models import get_models
from .preprocessing import build_preprocessor


@dataclass
class AutoTrainResult:
    best_model_name: Optional[str]
    best_estimator: Any
    best_accuracy: Optional[float]
    problem_type: str
    leaderboard: List[Dict[str, Any]]
    failed_models: List[Dict[str, Any]]
    feature_columns: List[str]
    metadata: Dict[str, Any]


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        value = float(value)
        if np.isnan(value) or np.isinf(value):
            return None
        return value
    except Exception:
        return None


def detect_task_type(df: pd.DataFrame, target_column: str) -> str:
    y = df[target_column]
    if pd.api.types.is_float_dtype(y):
        return "regression"
    if pd.api.types.is_integer_dtype(y):
        unique_count = int(y.nunique(dropna=True))
        return "classification" if unique_count <= min(20, max(2, int(len(y) * 0.1))) else "regression"
    if pd.api.types.is_bool_dtype(y) or pd.api.types.is_object_dtype(y) or pd.api.types.is_string_dtype(y):
        return "classification"
    if pd.api.types.is_numeric_dtype(y):
        return "classification" if y.nunique(dropna=True) <= 20 else "regression"
    return "classification"


def _cv_folds(y: pd.Series, problem_type: str) -> int:
    if len(y) < 6:
        return 0
    if problem_type == "classification":
        counts = y.value_counts(dropna=False)
        if counts.empty or counts.min() < 2:
            return 0
        return int(max(2, min(5, counts.min())))
    return int(max(2, min(5, len(y) // 4)))


def _classification_metrics(y_true, y_pred) -> Dict[str, Optional[float]]:
    return {
        "accuracy": safe_float(accuracy_score(y_true, y_pred)),
        "precision": safe_float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall": safe_float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_score": safe_float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "r2_score": None,
        "mae": None,
        "rmse": None,
    }


def _regression_metrics(y_true, y_pred) -> Dict[str, Optional[float]]:
    mae = safe_float(mean_absolute_error(y_true, y_pred))
    rmse = safe_float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = safe_float(r2_score(y_true, y_pred))
    return {
        "accuracy": r2,
        "precision": None,
        "recall": None,
        "f1_score": None,
        "r2_score": r2,
        "mae": mae,
        "rmse": rmse,
    }


def prepare_xy(df: pd.DataFrame, target_column: str):
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' was not found.")
    work = df.replace([np.inf, -np.inf], np.nan).dropna(subset=[target_column]).copy()
    if work.empty:
        raise ValueError("No usable rows remain after removing missing target values.")
    feature_columns = [c for c in work.columns if c != target_column]
    if not feature_columns:
        raise ValueError("At least one feature column is required.")
    return work[feature_columns], work[target_column], feature_columns


def train_model_set(df: pd.DataFrame, target_column: str) -> AutoTrainResult:
    X, y, feature_columns = prepare_xy(df, target_column)
    problem_type = detect_task_type(df, target_column)
    if problem_type == "regression":
        y = pd.to_numeric(y, errors="coerce")
        valid = y.notna()
        X = X.loc[valid]
        y = y.loc[valid]

    if len(X) < 5:
        raise ValueError("At least five valid rows are required for training.")

    stratify = None
    if problem_type == "classification":
        counts = y.value_counts(dropna=False)
        if len(counts) > 1 and counts.min() >= 2:
            stratify = y

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=stratify
    )
    models = get_models(problem_type)
    leaderboard: List[Dict[str, Any]] = []
    failed_models: List[Dict[str, Any]] = []
    trained: Dict[str, Any] = {}

    for model_name, estimator in models.items():
        started = time.perf_counter()
        row = {
            "model_name": model_name,
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "r2_score": None,
            "mae": None,
            "rmse": None,
            "cv_score": None,
            "training_time": None,
            "status": "failed",
            "error": "",
        }
        try:
            pipeline = Pipeline(steps=[("preprocessor", build_preprocessor(X)), ("model", estimator)])
            pipeline.fit(X_train, y_train)
            predictions = pipeline.predict(X_test)
            metrics = (
                _classification_metrics(y_test, predictions)
                if problem_type == "classification"
                else _regression_metrics(y_test, predictions)
            )
            row.update(metrics)
            folds = _cv_folds(y, problem_type)
            if folds:
                scoring = "accuracy" if problem_type == "classification" else "r2"
                row["cv_score"] = safe_float(cross_val_score(pipeline, X, y, cv=folds, scoring=scoring).mean())
            row["training_time"] = round(time.perf_counter() - started, 4)
            row["status"] = "success" if row.get("accuracy") is not None else "failed"
            if row["status"] == "success":
                trained[model_name] = pipeline
            else:
                row["error"] = "Model trained but did not produce a valid comparison score."
        except Exception as exc:
            row["training_time"] = round(time.perf_counter() - started, 4)
            row["error"] = str(exc)[:500]
            failed_models.append({"model_name": model_name, "error": row["error"]})
        leaderboard.append(row)

    valid_results = [r for r in leaderboard if r.get("accuracy") is not None]
    valid_results.sort(key=lambda r: float(r["accuracy"]), reverse=True)
    invalid_results = [r for r in leaderboard if r.get("accuracy") is None]
    sorted_leaderboard = valid_results + invalid_results

    if not valid_results:
        raise RuntimeError("No model produced a valid score. Failed models were logged in the leaderboard.")

    best_row = valid_results[0]
    best_name = best_row["model_name"]
    final_model = get_models(problem_type)[best_name]
    final_pipeline = Pipeline(steps=[("preprocessor", build_preprocessor(X)), ("model", final_model)])
    final_pipeline.fit(X, y)

    metadata = {
        "target_column": target_column,
        "problem_type": problem_type,
        "feature_columns": feature_columns,
        "rows_used": int(len(X)),
        "selected_by": "highest valid accuracy" if problem_type == "classification" else "highest valid R2 score",
        "best_metrics": best_row,
    }
    return AutoTrainResult(
        best_model_name=best_name,
        best_estimator=final_pipeline,
        best_accuracy=best_row.get("accuracy"),
        problem_type=problem_type,
        leaderboard=sorted_leaderboard,
        failed_models=failed_models,
        feature_columns=feature_columns,
        metadata=metadata,
    )


def save_best_model(result: AutoTrainResult, dataset_name: str) -> Dict[str, str]:
    safe_dataset = "".join(ch if ch.isalnum() else "_" for ch in dataset_name.rsplit(".", 1)[0]).strip("_")
    safe_model = "".join(ch if ch.isalnum() else "_" for ch in (result.best_model_name or "model")).strip("_")
    model_dir = os.path.join(settings.MEDIA_ROOT, "models")
    os.makedirs(model_dir, exist_ok=True)
    base = f"{safe_dataset}_{safe_model}_{int(time.time())}"
    joblib_path = os.path.join(model_dir, f"{base}.joblib")
    pickle_path = os.path.join(model_dir, f"{base}.pkl")
    payload = {
        "pipeline": result.best_estimator,
        "metadata": result.metadata,
        "leaderboard": result.leaderboard,
    }
    joblib.dump(payload, joblib_path)
    with open(pickle_path, "wb") as handle:
        pickle.dump(payload, handle)
    return {"joblib_path": joblib_path, "pickle_path": pickle_path}


def predict_dataframe(payload: Dict[str, Any], df: pd.DataFrame) -> List[Any]:
    pipeline = payload.get("pipeline")
    metadata = payload.get("metadata", {})
    feature_columns = metadata.get("feature_columns", [])
    if pipeline is None:
        raise ValueError("Saved model payload does not contain a pipeline.")
    missing = [c for c in feature_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required feature columns: {', '.join(missing)}")
    predictions = pipeline.predict(df[feature_columns])
    return [value.item() if hasattr(value, "item") else value for value in predictions]
