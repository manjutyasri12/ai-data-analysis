from typing import Any, Dict

from sklearn.ensemble import (
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures
from sklearn.svm import SVC, SVR
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor


def regression_models() -> Dict[str, Any]:
    return {
        "Linear Regression": LinearRegression(),
        "Polynomial Regression": Pipeline(
            steps=[
                ("polynomial_features", PolynomialFeatures(degree=2, include_bias=False)),
                ("linear_regression", LinearRegression()),
            ]
        ),
        "Decision Tree Regressor": DecisionTreeRegressor(random_state=42),
        "Random Forest Regressor": RandomForestRegressor(
            n_estimators=160, random_state=42, n_jobs=-1
        ),
        "SVR": SVR(kernel="rbf", C=10.0, gamma="scale"),
        "Gradient Boosting Regressor": GradientBoostingRegressor(random_state=42),
    }


def classification_models() -> Dict[str, Any]:
    return {
        "Logistic Regression": LogisticRegression(max_iter=1500, random_state=42),
        "Decision Tree Classifier": DecisionTreeClassifier(random_state=42),
        "Random Forest Classifier": RandomForestClassifier(
            n_estimators=160, random_state=42, n_jobs=-1
        ),
        "SVM": SVC(kernel="rbf", probability=True, random_state=42),
        "KNN": KNeighborsClassifier(n_neighbors=5),
        "GaussianNB": GaussianNB(),
    }


def get_models(problem_type: str) -> Dict[str, Any]:
    if problem_type == "classification":
        return classification_models()
    return regression_models()


def all_model_names() -> Dict[str, list]:
    return {
        "regression": list(regression_models().keys()),
        "classification": list(classification_models().keys()),
    }
