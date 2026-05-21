"""
Complete ML Models Registry for Regression and Classification.

This module provides:
1. REGRESSION_MODELS - All 6 regression models
2. CLASSIFICATION_MODELS - All 6 classification models
3. Helper functions for model training and evaluation
"""

from typing import Any, Dict
import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.svm import SVR, SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline


# ============================================================================
# REGRESSION MODELS (6 total)
# ============================================================================

REGRESSION_MODELS: Dict[str, Any] = {
    "Linear Regression": LinearRegression(),
    
    "Polynomial Regression": Pipeline(
        steps=[
            ("poly_features", PolynomialFeatures(degree=2, include_bias=False)),
            ("linear_reg", LinearRegression()),
        ]
    ),
    
    "Decision Tree Regressor": DecisionTreeRegressor(
        random_state=42,
        max_depth=10,
    ),
    
    "Random Forest Regressor": RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        n_jobs=-1,
        max_depth=15,
    ),
    
    "SVR": SVR(
        kernel="rbf",
        C=100.0,
        gamma="scale",
    ),
    
    "Gradient Boosting Regressor": GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42,
    ),
}


# ============================================================================
# CLASSIFICATION MODELS (6 total)
# ============================================================================

CLASSIFICATION_MODELS: Dict[str, Any] = {
    "Logistic Regression": LogisticRegression(
        max_iter=1000,
        random_state=42,
        multi_class="multinomial",
    ),
    
    "Decision Tree Classifier": DecisionTreeClassifier(
        random_state=42,
        max_depth=10,
    ),
    
    "Random Forest Classifier": RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        n_jobs=-1,
        max_depth=15,
    ),
    
    "SVM": SVC(
        kernel="rbf",
        C=1.0,
        gamma="scale",
        probability=True,
        random_state=42,
    ),
    
    "KNN": KNeighborsClassifier(
        n_neighbors=5,
        n_jobs=-1,
    ),
    
    "Gaussian Naive Bayes": GaussianNB(),
}


def get_regression_models() -> Dict[str, Any]:
    """Get all regression models."""
    return {k: v.__class__(**v.get_params()) if hasattr(v, 'get_params') else v 
            for k, v in REGRESSION_MODELS.items()}


def get_classification_models() -> Dict[str, Any]:
    """Get all classification models."""
    return {k: v.__class__(**v.get_params()) if hasattr(v, 'get_params') else v 
            for k, v in CLASSIFICATION_MODELS.items()}


def get_all_model_names(problem_type: str = None) -> Dict[str, list]:
    """
    Get all available model names.
    
    Args:
        problem_type: 'regression', 'classification', or None (for all)
    
    Returns:
        dict with 'regression' and 'classification' lists
    """
    return {
        "regression": list(REGRESSION_MODELS.keys()),
        "classification": list(CLASSIFICATION_MODELS.keys()),
    }


def get_model(model_name: str, problem_type: str) -> Any:
    """
    Get a specific model instance by name and problem type.
    
    Args:
        model_name: Name of the model
        problem_type: 'regression' or 'classification'
    
    Returns:
        Model instance (fresh copy)
    """
    if problem_type == "regression":
        models = get_regression_models()
    elif problem_type == "classification":
        models = get_classification_models()
    else:
        raise ValueError(f"Unknown problem_type: {problem_type}")
    
    if model_name not in models:
        raise ValueError(f"Model '{model_name}' not found in {problem_type} models")
    
    return models[model_name]
