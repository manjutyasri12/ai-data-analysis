import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    r2_score,
)


def _safe_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        xf = float(x)
        if np.isnan(xf) or np.isinf(xf):
            return None
        return xf
    except Exception:
        return None


def compute_classification_metrics(
    y_true: np.ndarray, y_pred: np.ndarray
) -> Dict[str, float]:
    # Macro averaging works across binary/multi-class.
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average="macro", zero_division=0)
    rec = recall_score(y_true, y_pred, average="macro", zero_division=0)
    f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)

    return {
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
    }


def compute_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = float(np.sqrt(mse))

    return {
        "r2": float(r2),
        "mae": float(mae),
        "rmse": float(rmse),
    }


def evaluate_model(
    *,
    problem_type: str,
    estimator: Any,
    X_test: Any,
    y_test: Any,
) -> Tuple[Optional[Dict[str, float]], Optional[str]]:
    """Evaluate a trained pipeline.

    Returns (metrics_dict, error_string).
    metrics_dict contains only relevant keys for the problem type.
    """
    try:
        y_pred = estimator.predict(X_test)

        if problem_type == "classification":
            metrics = compute_classification_metrics(np.array(y_test), np.array(y_pred))
        else:
            metrics = compute_regression_metrics(np.array(y_test), np.array(y_pred))

        # Validate metric presence
        if problem_type == "classification":
            if "accuracy" not in metrics:
                return None, "Missing accuracy in classification metrics"
        else:
            if "r2" not in metrics:
                return None, "Missing r2 in regression metrics"

        return metrics, None

    except Exception as e:
        return None, str(e)[:500]


def select_best_model(
    leaderboard: List[Dict[str, Any]],
    *,
    problem_type: str,
) -> Optional[Dict[str, Any]]:
    """Select the best model row.

    leaderboard rows are expected to have:
    - status: tested
    - score: float
    """
    candidates = [r for r in leaderboard if r.get("status") == "tested" and r.get("score") is not None]
    if not candidates:
        return None
    return sorted(candidates, key=lambda r: float(r["score"]), reverse=True)[0]


