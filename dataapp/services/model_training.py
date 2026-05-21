"""
Model Training Service

Handles:
- Training individual models
- Computing comprehensive metrics
- Model evaluation and comparison
- Saving/loading trained models
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import joblib
import pickle
import io
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_absolute_error, mean_squared_error, r2_score
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from .ml_models import (
    get_regression_models, get_classification_models, get_model
)


def _safe_float(x: Any) -> Optional[float]:
    """Convert value to float safely, returning None if invalid."""
    if x is None:
        return None
    try:
        xf = float(x)
        if np.isnan(xf) or np.isinf(xf):
            return None
        return xf
    except (TypeError, ValueError):
        return None


def build_preprocessor(
    df: pd.DataFrame,
    feature_cols: List[str]
) -> ColumnTransformer:
    """Build a preprocessing pipeline."""
    numeric_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = [c for c in feature_cols if c not in numeric_cols]
    
    transformers = []
    
    if numeric_cols:
        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler()),
        ])
        transformers.append(('num', numeric_transformer, numeric_cols))
    
    if categorical_cols:
        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
        ])
        transformers.append(('cat', categorical_transformer, categorical_cols))
    
    return ColumnTransformer(transformers=transformers, remainder='drop')


def compute_regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> Dict[str, Optional[float]]:
    """Compute regression metrics."""
    metrics = {}
    
    try:
        metrics['mae'] = _safe_float(mean_absolute_error(y_true, y_pred))
        metrics['rmse'] = _safe_float(np.sqrt(mean_squared_error(y_true, y_pred)))
        metrics['r2_score'] = _safe_float(r2_score(y_true, y_pred))
        
        # For regression, use R2 as primary accuracy metric
        metrics['accuracy'] = metrics['r2_score']
        metrics['precision'] = None
        metrics['recall'] = None
        metrics['f1_score'] = None
    except Exception as e:
        print(f"Error computing regression metrics: {e}")
        metrics['mae'] = None
        metrics['rmse'] = None
        metrics['r2_score'] = None
        metrics['accuracy'] = None
    
    return metrics


def compute_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> Dict[str, Optional[float]]:
    """Compute classification metrics."""
    metrics = {}
    
    try:
        metrics['accuracy'] = _safe_float(accuracy_score(y_true, y_pred))
        metrics['precision'] = _safe_float(
            precision_score(y_true, y_pred, average='macro', zero_division=0)
        )
        metrics['recall'] = _safe_float(
            recall_score(y_true, y_pred, average='macro', zero_division=0)
        )
        metrics['f1_score'] = _safe_float(
            f1_score(y_true, y_pred, average='macro', zero_division=0)
        )
        
        # For classification, no regression metrics
        metrics['mae'] = None
        metrics['rmse'] = None
        metrics['r2_score'] = None
    except Exception as e:
        print(f"Error computing classification metrics: {e}")
        metrics['accuracy'] = None
        metrics['precision'] = None
        metrics['recall'] = None
        metrics['f1_score'] = None
    
    return metrics


def train_single_model(
    model_name: str,
    model: Any,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    problem_type: str,
    preprocessor: Optional[ColumnTransformer] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Train a single model and compute metrics.
    
    Returns:
        (result_dict, error_string)
    """
    try:
        # Build pipeline with preprocessor if provided
        if preprocessor:
            pipe = Pipeline(steps=[
                ('preprocessor', preprocessor),
                ('model', model)
            ])
        else:
            pipe = model
        
        # Train
        pipe.fit(X_train, y_train)
        
        # Predict
        y_pred = pipe.predict(X_test)
        
        # Compute metrics
        if problem_type == "classification":
            metrics = compute_classification_metrics(
                np.array(y_test),
                np.array(y_pred)
            )
        else:
            metrics = compute_regression_metrics(
                np.array(y_test),
                np.array(y_pred)
            )
        
        # Filter out None values for cleaner results
        metrics_clean = {k: v for k, v in metrics.items() if v is not None}
        
        # Use accuracy as the primary score
        accuracy = metrics.get('accuracy')
        if accuracy is None:
            return None, "No valid accuracy metric computed"
        
        result = {
            'model_name': model_name,
            'accuracy': round(float(accuracy), 6),
            'metrics': metrics_clean,
            'trained': True,
            'error': None,
            'model': pipe  # Store the trained model for serialization
        }
        
        return result, None
        
    except Exception as e:
        error_msg = str(e)[:500]
        return None, error_msg


def auto_train_all_models(
    df: pd.DataFrame,
    target_column: str,
    problem_type: str = "regression",
    test_size: float = 0.2
) -> List[Dict[str, Any]]:
    """
    Train ALL available models and return results.
    
    Args:
        df: DataFrame with features and target
        target_column: Name of target column
        problem_type: 'regression' or 'classification'
        test_size: Test split fraction
    
    Returns:
        List of results sorted by accuracy (highest first)
    """
    
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not in DataFrame")
    
    # Prepare data
    feature_cols = [c for c in df.columns if c != target_column]
    X = df[feature_cols].copy()
    y = df[target_column].copy()
    
    # Remove rows with missing target
    valid_idx = y.notna()
    X = X[valid_idx]
    y = y[valid_idx]
    
    if len(X) < 5:
        raise ValueError("Not enough valid samples to train models")
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=42
    )
    
    # Build preprocessor
    preprocessor = build_preprocessor(X, feature_cols)
    
    # Get models based on problem type
    if problem_type == "classification":
        models_dict = get_classification_models()
    else:
        models_dict = get_regression_models()
    
    # Train all models
    results = []
    for model_name, model_obj in models_dict.items():
        result, error = train_single_model(
            model_name=model_name,
            model=model_obj,
            X_train=X_train,
            X_test=X_test,
            y_train=y_train,
            y_test=y_test,
            problem_type=problem_type,
            preprocessor=preprocessor
        )
        
        if error:
            results.append({
                'model_name': model_name,
                'accuracy': None,
                'trained': False,
                'error': error,
                'metrics': {}
            })
        else:
            results.append(result)
    
    # Filter valid results and sort by accuracy
    valid_results = [r for r in results if r['accuracy'] is not None]
    valid_results.sort(key=lambda x: x['accuracy'], reverse=True)
    
    # Add invalid results at the end
    invalid_results = [r for r in results if r['accuracy'] is None]
    
    return valid_results + invalid_results


def get_best_model_name(results: List[Dict[str, Any]]) -> Optional[str]:
    """Get the name of the best model from results."""
    for result in results:
        if result.get('accuracy') is not None and result.get('trained'):
            return result.get('model_name')
    return None


def format_results_for_display(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format results for display in templates."""
    display_results = []
    
    for r in results:
        if r.get('trained'):
            metrics = r.get('metrics', {})
            display_result = {
                'model_name': r.get('model_name'),
                'accuracy': r.get('accuracy'),
                'precision': metrics.get('precision'),
                'recall': metrics.get('recall'),
                'f1_score': metrics.get('f1_score'),
                'mae': metrics.get('mae'),
                'rmse': metrics.get('rmse'),
                'r2_score': metrics.get('r2_score'),
                'status': 'success'
            }
        else:
            display_result = {
                'model_name': r.get('model_name'),
                'accuracy': None,
                'precision': None,
                'recall': None,
                'f1_score': None,
                'mae': None,
                'rmse': None,
                'r2_score': None,
                'status': 'failed',
                'error': r.get('error')
            }
        
        display_results.append(display_result)
    
    return display_results


def serialize_model_to_bytes(model: Any, format: str = 'joblib') -> bytes:
    """Serialize a trained model to bytes."""
    buffer = io.BytesIO()
    if format == 'pickle':
        pickle.dump(model, buffer)
    else:  # joblib
        joblib.dump(model, buffer)
    buffer.seek(0)
    return buffer.getvalue()


def serialize_model_to_file(model: Any, filepath: str, format: str = 'joblib') -> None:
    """Save a trained model to a file."""
    if format == 'pickle':
        with open(filepath, 'wb') as f:
            pickle.dump(model, f)
    else:  # joblib
        joblib.dump(model, filepath)


def deserialize_model(filepath: str, format: str = 'joblib') -> Any:
    """Load a trained model from a file."""
    if format == 'pickle':
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    else:  # joblib
        return joblib.load(filepath)
