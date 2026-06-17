from io import StringIO
import logging
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


logger = logging.getLogger(__name__)


def safe_json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def dataframe_to_session_json(df: pd.DataFrame) -> str:
    return df.to_json(orient="split", date_format="iso")


def dataframe_from_session_json(data_json: str) -> pd.DataFrame:
    return pd.read_json(StringIO(data_json), orient="split")


def column_groups(df: pd.DataFrame) -> Dict[str, List[str]]:
    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical = [c for c in df.columns if c not in numeric]
    return {"numeric": numeric, "categorical": categorical}


def dataset_overview(df: pd.DataFrame) -> Dict[str, Any]:
    groups = column_groups(df)
    return {
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "dataset_size": f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB",
        "memory_usage": f"{df.memory_usage(deep=True).sum() / (1024 ** 2):.4f} MB",
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "missing_values": {c: int(v) for c, v in df.isna().sum().items()},
        "duplicate_rows": int(df.duplicated().sum()),
        "numerical_columns": groups["numeric"],
        "categorical_columns": groups["categorical"],
        "column_names": df.columns.tolist(),
    }


def clean_dataset_for_display(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    logger.info(
        "clean_dataset_for_display entry: shape=%s columns=%s",
        df.shape,
        df.columns.tolist(),
    )
    if "Monthly_Salary" in df.columns:
        salary_before = pd.to_numeric(df["Monthly_Salary"], errors="coerce")
        logger.info(
            "Monthly_Salary before cleaning: dtype=%s numeric_dtype=%s stats=%s negative_count=%s sentinel_999999_count=%s",
            df["Monthly_Salary"].dtype,
            salary_before.dtype,
            salary_before.describe().to_dict(),
            int((salary_before < 0).sum()),
            int((salary_before == 999999).sum()),
        )

    cleaned = df.copy()
    report: Dict[str, Any] = {
        "missing_values": [],
        "duplicates_removed": 0,
        "label_encodings": [],
        "outliers": [],
        "domain_rules": [],
        "scaling": "Feature scaling is applied inside the ML pipeline with StandardScaler.",
        "summary": [],
    }
    duplicate_count = int(cleaned.duplicated().sum())
    if duplicate_count:
        cleaned = cleaned.drop_duplicates().reset_index(drop=True)
    report["duplicates_removed"] = duplicate_count
    report["summary"].append(f"Removed {duplicate_count} duplicate rows.")

    for col in cleaned.columns:
        cleaned[col] = pd.to_numeric(cleaned[col], errors="ignore")

    if "Monthly_Salary" in cleaned.columns:
        cleaned["Monthly_Salary"] = pd.to_numeric(cleaned["Monthly_Salary"], errors="coerce")
        invalid_salary_mask = (cleaned["Monthly_Salary"] <= 0) | (cleaned["Monthly_Salary"] == 999999)
        invalid_salary_count = int(invalid_salary_mask.sum())
        valid_salary = cleaned.loc[~invalid_salary_mask, "Monthly_Salary"].dropna()
        replacement = valid_salary.median()

        if invalid_salary_count and not pd.isna(replacement):
            cleaned.loc[invalid_salary_mask, "Monthly_Salary"] = replacement
            report["domain_rules"].append(
                {
                    "column": "Monthly_Salary",
                    "rule": "Salary must be positive and must not use the 999999 sentinel value",
                    "fixed_values": invalid_salary_count,
                    "replacement": safe_json_value(replacement),
                }
            )
            logger.info(
                "Monthly_Salary domain rule applied: fixed_values=%s replacement=%s",
                invalid_salary_count,
                replacement,
            )
        else:
            logger.info(
                "Monthly_Salary domain rule skipped: invalid_count=%s replacement=%s",
                invalid_salary_count,
                replacement,
            )

    groups = column_groups(cleaned)
    for col in groups["numeric"]:
        if cleaned[col].isna().any():
            median = cleaned[col].median()
            fill_value = 0 if pd.isna(median) else median
            cleaned[col] = cleaned[col].fillna(fill_value)
            report["missing_values"].append({"column": col, "strategy": "median", "value": safe_json_value(fill_value)})
    for col in groups["categorical"]:
        if cleaned[col].isna().any():
            mode = cleaned[col].mode(dropna=True)
            fill_value = mode.iloc[0] if not mode.empty else "Missing"
            cleaned[col] = cleaned[col].fillna(fill_value)
            report["missing_values"].append({"column": col, "strategy": "most frequent", "value": safe_json_value(fill_value)})
    for col in groups["numeric"]:
        q1 = cleaned[col].quantile(0.25)
        q3 = cleaned[col].quantile(0.75)
        iqr = q3 - q1
        if pd.isna(iqr) or iqr == 0:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        mask = (cleaned[col] < lower) | (cleaned[col] > upper)
        count = int(mask.sum())
        if count:
            cleaned[col] = cleaned[col].clip(lower, upper)
            report["outliers"].append({"column": col, "capped": count, "lower": round(float(lower), 6), "upper": round(float(upper), 6)})
            if col == "Monthly_Salary":
                logger.info(
                    "Monthly_Salary IQR capping executed: capped=%s lower=%s upper=%s",
                    count,
                    lower,
                    upper,
                )
    for col in groups["categorical"]:
        unique_count = cleaned[col].nunique(dropna=True)
        if 1 < unique_count <= 50:
            categories = sorted([v for v in cleaned[col].dropna().unique()], key=lambda v: str(v))
            mapping = {str(value): i for i, value in enumerate(categories)}
            cleaned[col] = cleaned[col].map(lambda v: mapping.get(str(v), -1))
            report["label_encodings"].append({"column": col, "mapping": mapping})
    report["summary"].append("No missing values required filling." if not report["missing_values"] else f"Handled missing values in {len(report['missing_values'])} columns.")
    report["summary"].append(f"Applied {len(report['domain_rules'])} domain-specific cleaning rules.")
    report["summary"].append(f"Encoded {len(report['label_encodings'])} categorical columns.")
    report["summary"].append(f"Capped outliers in {len(report['outliers'])} numeric columns.")
    if "Monthly_Salary" in cleaned.columns:
        salary_after = pd.to_numeric(cleaned["Monthly_Salary"], errors="coerce")
        logger.info(
            "Monthly_Salary after cleaning: dtype=%s stats=%s negative_count=%s sentinel_999999_count=%s",
            cleaned["Monthly_Salary"].dtype,
            salary_after.describe().to_dict(),
            int((salary_after < 0).sum()),
            int((salary_after == 999999).sum()),
        )
    logger.info("clean_dataset_for_display exit: shape=%s", cleaned.shape)
    return cleaned, report


def changed_table_html(raw_df: pd.DataFrame, cleaned_df: pd.DataFrame, max_rows: int = 100) -> str:
    raw = raw_df.head(max_rows).reset_index(drop=True)
    clean = cleaned_df.head(max_rows).reset_index(drop=True)
    headers = "".join(f"<th>{col}</th>" for col in clean.columns)
    rows = []
    for row_idx in range(len(clean)):
        cells = []
        for col in clean.columns:
            new_value = clean.loc[row_idx, col]
            old_value = raw.loc[row_idx, col] if row_idx < len(raw) and col in raw.columns else None
            changed = not ((pd.isna(old_value) and pd.isna(new_value)) or old_value == new_value)
            cls = " class=\"changed-cell\"" if changed else ""
            display = "" if pd.isna(new_value) else safe_json_value(new_value)
            cells.append(f"<td{cls}>{display}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return '<table class="table table-sm table-striped table-hover align-middle">' + f"<thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def one_hot_encoder():
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    numeric = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical = [c for c in X.columns if c not in numeric]
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline(steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), numeric))
    if categorical:
        transformers.append(("cat", Pipeline(steps=[("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", one_hot_encoder())]), categorical))
    return ColumnTransformer(transformers=transformers, remainder="drop")
