import os
import json
import warnings
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, r2_score, mean_squared_error, silhouette_score
from sklearn.model_selection import train_test_split

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import PolynomialFeatures

from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.svm import SVC, SVR
from sklearn.naive_bayes import GaussianNB
from sklearn.cluster import KMeans, DBSCAN
from sklearn.neighbors import NearestNeighbors

from sklearn.ensemble import IsolationForest

# xgboost is optional; keep imports safe
try:
    from xgboost import XGBClassifier, XGBRegressor
    _HAS_XGBOOST = True
except Exception:
    _HAS_XGBOOST = False

warnings.filterwarnings("ignore")


@dataclass
class TrainResult:
    best_model_name: str
    best_estimator: Any
    best_score: float
    leaderboard: List[Dict[str, Any]]
    problem_type: str
    dataset_type: str


def _safe_read_json_df(data_json: str) -> pd.DataFrame:
    return pd.read_json(data_json)


def load_df_from_session(request) -> pd.DataFrame:
    data_json = request.session.get("data")
    if not data_json:
        raise ValueError("No dataset found in session. Please upload a CSV first.")
    return _safe_read_json_df(data_json)


def remove_all_null_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(axis=1, how="all")


def preprocess_dataframe(
    df: pd.DataFrame,
    target_column: str,
    *,
    outlier_strategy: str = "remove"  # "remove" or "cap" (cap not implemented fully)
) -> Tuple[pd.DataFrame, Pipeline, Dict[str, Any]]:
    if target_column not in df.columns:
        raise ValueError(f"target_column '{target_column}' not found in dataset")

    df = df.copy()
    df = remove_all_null_columns(df)

    # Remove duplicates
    df = df.drop_duplicates()

    feature_cols = [c for c in df.columns if c != target_column]
    numeric_feature_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()

    outlier_counts: Dict[str, Any] = {}
    if len(numeric_feature_cols) >= 2:
        iso = IsolationForest(contamination="auto", random_state=42)
        X_num = df[numeric_feature_cols].replace([np.inf, -np.inf], np.nan)
        iso.fit(X_num)
        preds = iso.predict(X_num)  # -1 outliers, 1 inliers
        outliers = np.where(preds == -1)[0]
        outlier_counts["numeric_outliers"] = int(len(outliers))
        if outlier_strategy == "remove" and len(outliers) > 0:
            df = df.drop(index=df.index[outliers])
    else:
        outlier_counts["numeric_outliers"] = 0

    categorical_cols = [c for c in feature_cols if c not in numeric_feature_cols]

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_feature_cols),
            ("cat", categorical_transformer, categorical_cols),
        ],
        remainder="drop",
    )

    df = df.dropna(subset=[target_column])

    X = df[feature_cols]
    preprocessor.fit(X)

    meta = {
        "feature_columns": feature_cols,
        "numeric_feature_columns": numeric_feature_cols,
        "categorical_feature_columns": categorical_cols,
        "outliers": outlier_counts,
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
    }

    return df, preprocessor, meta


def detect_dataset_type(df: pd.DataFrame, target_column: Optional[str] = None) -> str:
    """Auto-detect task type using explicit rules:

    - float -> regression
    - integer with few unique values -> classification
    - object/string -> classification

    Falls back to heuristics for other cases.
    """

    object_cols = df.select_dtypes(include=["object"]).columns.tolist()

    if any("text" in c.lower() or "review" in c.lower() or "message" in c.lower() for c in object_cols):
        return "nlp_text"

    if any("image" in c.lower() or "pixel" in c.lower() or "img" in c.lower() for c in object_cols):
        return "image"

    dt_cols = []
    for c in df.columns:
        if "date" in c.lower() or "time" in c.lower() or "timestamp" in c.lower():
            dt_cols.append(c)
    if dt_cols:
        return "time_series"

    if target_column is None or target_column not in df.columns:
        return "clustering"

    y = df[target_column]

    # Your explicit rules
    if pd.api.types.is_float_dtype(y):
        return "regression"

    if pd.api.types.is_integer_dtype(y):
        nunique = int(y.nunique(dropna=True))
        if nunique <= 20:
            return "classification"
        return "regression"

    if y.dtype == "O" or pd.api.types.is_string_dtype(y) or pd.api.types.is_categorical_dtype(y):
        return "classification"

    # Fallback heuristics
    if pd.api.types.is_numeric_dtype(y):
        nunique = int(y.nunique(dropna=True))
        if nunique <= 20:
            return "classification"
        return "regression"

    return "classification"


def recommend_models(dataset_type: str, target_column: str) -> List[str]:
    if dataset_type == "classification":
        return ["Logistic Regression", "Random Forest", "XGBoost", "SVM", "Decision Tree", "Naive Bayes"]
    if dataset_type == "regression":
        return ["Linear Regression", "Decision Tree", "Random Forest", "XGBoost", "SVR"]
    if dataset_type == "clustering":
        return ["K-Means", "DBSCAN"]
    if dataset_type == "time_series":
        return ["ARIMA", "LSTM"]
    if dataset_type == "nlp_text":
        return ["Naive Bayes", "BERT"]
    if dataset_type == "image":
        return ["CNN"]
    return []


def _build_models(dataset_type: str, random_state: int = 42) -> Dict[str, Any]:
    models: Dict[str, Any] = {}

    if dataset_type == "classification":
        models["Logistic Regression"] = LogisticRegression(max_iter=1000)
        models["Random Forest"] = RandomForestClassifier(n_estimators=300, random_state=random_state)
        models["Decision Tree"] = DecisionTreeClassifier(random_state=random_state)
        models["SVM"] = SVC(probability=True)
        models["Naive Bayes"] = GaussianNB()
        if _HAS_XGBOOST:
            models["XGBoost"] = XGBClassifier(
                n_estimators=500,
                learning_rate=0.05,
                max_depth=5,
                subsample=0.8,
                colsample_bytree=0.8,
                eval_metric="logloss",
                random_state=random_state,
            )

    elif dataset_type == "regression":
        models["Linear Regression"] = LinearRegression()
        models["Polynomial Regression (deg=2)"] = Pipeline(
            steps=[
                ("poly", PolynomialFeatures(degree=2, include_bias=False)),
                ("reg", LinearRegression()),
            ]
        )
        models["Decision Tree"] = DecisionTreeRegressor(random_state=random_state)
        models["Random Forest"] = RandomForestRegressor(n_estimators=300, random_state=random_state)
        models["SVR"] = SVR()
        if _HAS_XGBOOST:
            models["XGBoost"] = XGBRegressor(
                n_estimators=800,
                learning_rate=0.05,
                max_depth=6,
                subsample=0.85,
                colsample_bytree=0.85,
                random_state=random_state,
            )

    return models


def auto_train_and_select(df: pd.DataFrame, target_column: str) -> TrainResult:
    dataset_type = detect_dataset_type(df, target_column)

    if dataset_type == "clustering":
        df2 = remove_all_null_columns(df.copy())
        feature_cols = [c for c in df2.columns if c != target_column]
        numeric_feature_cols = df2[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_feature_cols) < 2:
            raise ValueError("Clustering requires at least 2 numeric feature columns (excluding target_column).")

        X = df2[numeric_feature_cols].replace([np.inf, -np.inf], np.nan).dropna()
        if len(X) < 5:
            raise ValueError("Not enough rows after cleaning to run clustering.")

        X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)

        models = {
            "K-Means": KMeans(
                n_clusters=min(5, max(2, int(np.sqrt(len(X_train))))),
                random_state=42,
                n_init="auto",
            ),
            "DBSCAN": DBSCAN(eps=0.5, min_samples=5),
        }

        leaderboard: List[Dict[str, Any]] = []
        best_name = None
        best_estimator = None
        best_score: Optional[float] = None

        for name, model in models.items():
            try:
                model.fit(X_train)
                labels = model.predict(X_test) if hasattr(model, "predict") else model.fit_predict(X_test)

                if len(set(labels)) <= 1:
                    score = -1.0
                else:
                    score = float(silhouette_score(X_test, labels))

                leaderboard.append({"model": name, "score": round(score, 6)})
                if best_score is None or score > best_score:
                    best_score = score
                    best_name = name
                    best_estimator = model
            except Exception:
                continue

        if best_estimator is None:
            raise RuntimeError("No clustering model could be trained successfully.")

        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "num",
                    Pipeline(
                        steps=[
                            ("imputer", SimpleImputer(strategy="median")),
                            ("scaler", StandardScaler()),
                        ]
                    ),
                    numeric_feature_cols,
                )
            ],
            remainder="drop",
        )
        preprocessor.fit(df2[numeric_feature_cols])

        best_estimator.fit(preprocessor.transform(df2[numeric_feature_cols]))

        class _ClusteringPredictor:
            def __init__(self, pre, model):
                self.pre = pre
                self.model = model

            def predict(self, X_df: pd.DataFrame):
                X_tr = self.pre.transform(X_df[numeric_feature_cols])
                if hasattr(self.model, "predict"):
                    return self.model.predict(X_tr)
                if hasattr(self.model, "fit_predict"):
                    return self.model.fit_predict(X_tr)
                return getattr(self.model, "labels_", np.zeros(X_tr.shape[0], dtype=int))

        predictor = _ClusteringPredictor(preprocessor, best_estimator)

        return TrainResult(
            best_model_name=best_name,
            best_estimator=predictor,
            best_score=float(best_score),
            leaderboard=sorted(leaderboard, key=lambda x: x["score"], reverse=True),
            problem_type="clustering",
            dataset_type=dataset_type,
        )

    if dataset_type in {"time_series", "nlp_text", "image"}:
        return TrainResult(
            best_model_name=f"Auto training not implemented for {dataset_type} in CSV demo",
            best_estimator=None,
            best_score=-1.0,
            leaderboard=[],
            problem_type=dataset_type,
            dataset_type=dataset_type,
        )

    cleaned_df, preprocessor, meta = preprocess_dataframe(df, target_column)

    feature_cols = meta["feature_columns"]
    X = cleaned_df[feature_cols]
    y = cleaned_df[target_column]

    problem_type = "classification" if dataset_type == "classification" else "regression"

    stratify_y = None
    if problem_type == "classification":
        vc = y.value_counts(dropna=False)
        if vc.shape[0] >= 2 and vc.min() >= 2:
            stratify_y = y

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=stratify_y,
    )

    models = _build_models(dataset_type)

    trained_rows: List[Dict[str, Any]] = []
    failed_rows: List[Dict[str, Any]] = []

    best_name = None
    best_estimator = None
    best_score: Optional[float] = None

    import time

    for name, model in models.items():
        try:
            pipe = Pipeline(steps=[("pre", preprocessor), ("model", model)])

            start = time.time()
            pipe.fit(X_train, y_train)
            train_time_sec = float(time.time() - start)

            if problem_type == "classification":
                y_pred = pipe.predict(X_test)
                score = float(accuracy_score(y_test, y_pred))
            else:
                y_pred = pipe.predict(X_test)
                score = float(r2_score(y_test, y_pred))

            # IMPORTANT: never include None scores
            trained_rows.append({
                "model": name,
                "score": round(score, 6),
                "train_time_sec": round(train_time_sec, 4),
            })

            if best_score is None or score > best_score:
                best_score = score
                best_name = name
                best_estimator = pipe

        except Exception as e:
            failed_rows.append({"model": name, "status": "failed", "error": str(e)[:500]})
            continue

    if best_estimator is None or best_name is None or best_score is None:
        raise RuntimeError("No model could be trained successfully. Try a different target column.")

    trained_rows_sorted = sorted(trained_rows, key=lambda x: x["score"], reverse=True)

    leaderboard: List[Dict[str, Any]] = []
    for row in trained_rows_sorted:
        leaderboard.append({
            "model": row.get("model"),
            "score": row.get("score"),
            "train_time_sec": row.get("train_time_sec"),
            "status": "tested",
        })

    for f in failed_rows:
        leaderboard.append({
            "model": f.get("model"),
            "score": None,
            "status": "failed",
            "error": f.get("error"),
        })

    # Re-train best model again for saving correctness
    best_model_obj = None
    for n, m in models.items():
        if n == best_name:
            best_model_obj = m
            break
    if best_model_obj is None:
        raise RuntimeError("Best model selection failed internally.")

    final_pipe = Pipeline(steps=[("pre", preprocessor), ("model", best_model_obj)])
    final_pipe.fit(X_train, y_train)

    return TrainResult(
        best_model_name=best_name,
        best_estimator=final_pipe,
        best_score=float(best_score),
        leaderboard=leaderboard,
        problem_type=problem_type,
        dataset_type=dataset_type,
    )


def generate_insights(df: pd.DataFrame, target_column: str) -> List[str]:
    if target_column not in df.columns:
        return []

    insights: List[str] = []

    missing = df.isna().sum().sort_values(ascending=False)
    top_missing = missing.head(3)
    if top_missing.iloc[0] > 0:
        insights.append(
            "Missing data detected. Consider cleaning features with highest null counts: "
            + ", ".join([f"{c} ({int(v)} nulls)" for c, v in top_missing.items()])
        )

    y = df[target_column]
    feature_cols = [c for c in df.columns if c != target_column]

    num_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
    if len(num_cols) > 0 and pd.api.types.is_numeric_dtype(y):
        corrs: Dict[str, float] = {}
        for c in num_cols:
            try:
                cor = df[[c, target_column]].corr(numeric_only=True).iloc[0, 1]
                corrs[c] = cor
            except Exception:
                continue
        if corrs:
            best = sorted(corrs.items(), key=lambda kv: abs(kv[1]), reverse=True)[:3]
            insights.append(
                "Top numeric features correlated with target: "
                + ", ".join([f"{c} (corr={v:.3f})" for c, v in best if v == v])
            )

    cat_cols = [c for c in feature_cols if c not in num_cols]
    for c in cat_cols[:3]:
        try:
            if pd.api.types.is_numeric_dtype(y):
                means = df.groupby(c)[target_column].mean().sort_values(ascending=False)
                top = means.head(1).index[0]
                insights.append(f"Feature '{c}' shows strong group differences in target (highest mean at '{top}').")
            else:
                counts = df.groupby(c)[target_column].value_counts(normalize=True)
                insights.append(f"Feature '{c}' may impact target distribution across categories.")
        except Exception:
            continue

    for c in df.columns:
        cl = c.lower()
        if "date" in cl or "time" in cl or "timestamp" in cl:
            try:
                parsed = pd.to_datetime(df[c], errors="coerce")
                if parsed.notna().sum() > 0:
                    weekend_mask = parsed.dt.dayofweek >= 5
                    if weekend_mask.any() and pd.api.types.is_numeric_dtype(y):
                        wknd_mean = y[weekend_mask].mean()
                        wd_mean = y[~weekend_mask].mean()
                        if wknd_mean == wknd_mean and wd_mean == wd_mean:
                            delta = wknd_mean - wd_mean
                            insights.append(
                                f"Target tends to be {'higher' if delta>0 else 'lower'} on weekends by ~{abs(delta):.3f}."
                            )
            except Exception:
                continue

    if not insights:
        insights.append("No strong automated insights could be extracted. Try choosing a different target column.")

    return insights


def dataset_understanding_payload(df: pd.DataFrame, target_column: str) -> Dict[str, Any]:
    dataset_type = detect_dataset_type(df, target_column)
    rec_models = recommend_models(dataset_type, target_column)

    label_map = {
        "classification": "Classification (Pass/Fail)",
        "regression": "Regression (House Price)",
        "clustering": "Clustering (Customer Segmentation)",
        "time_series": "Time Series (Stock Prediction)",
        "nlp_text": "NLP/Text (Sentiment Analysis)",
        "image": "Image Data (Image Classification)",
    }

    return {
        "dataset_type": label_map.get(dataset_type, dataset_type),
        "target_column": target_column,
        "recommended_models": rec_models,
        "columns": df.columns.tolist(),
    }


def save_trained_model(trained_pipeline: Any, model_name: str, meta: Dict[str, Any], *, out_dir: str = "media/models") -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"best_model_{model_name.replace(' ', '_').lower()}.joblib")
    payload = {"pipeline": trained_pipeline, "meta": meta}
    joblib.dump(payload, path)
    return path


def load_saved_model(model_path: str) -> Any:
    return joblib.load(model_path)


def predict_with_pipeline(pipeline: Any, df: pd.DataFrame, *, feature_columns: Optional[List[str]] = None) -> np.ndarray:
    if feature_columns:
        missing = [c for c in feature_columns if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required feature columns for prediction: {missing}")
        X = df[feature_columns]
    else:
        X = df
    return pipeline.predict(X)

