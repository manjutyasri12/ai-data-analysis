from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


def _safe_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except Exception:
        pass
    try:
        v = float(x)
    except Exception:
        return None
    if np.isnan(v) or np.isinf(v):
        return None
    return v


def _is_numeric_series(s: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(s)


def _quantiles(series: pd.Series, qs: Tuple[float, ...] = (0.05, 0.25, 0.5, 0.75, 0.95)) -> Dict[float, Optional[float]]:
    series = series.dropna()
    if series.empty:
        return {q: None for q in qs}
    out: Dict[float, Optional[float]] = {}
    for q in qs:
        try:
            out[q] = _safe_float(series.quantile(q))
        except Exception:
            out[q] = None
    return out


def _outlier_count_iqr(series: pd.Series) -> int:
    series = series.dropna()
    if len(series) < 4:
        return 0
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0 or pd.isna(iqr):
        return 0
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return int(((series < lower) | (series > upper)).sum())


def _skewness(series: pd.Series) -> Optional[float]:
    series = series.dropna()
    if len(series) < 3:
        return None
    return _safe_float(series.skew())


def _kurtosis(series: pd.Series) -> Optional[float]:
    series = series.dropna()
    if len(series) < 4:
        return None
    return _safe_float(series.kurtosis())


def _corr_for_numeric(df: pd.DataFrame, x: str, y: str) -> Optional[float]:
    if x not in df.columns or y not in df.columns:
        return None
    sub = df[[x, y]].dropna()
    if sub.empty:
        return None
    if not (_is_numeric_series(sub[x]) and _is_numeric_series(sub[y])):
        return None
    try:
        c = sub[x].corr(sub[y])
        return _safe_float(c)
    except Exception:
        return None


def _top_categories_counts(series: pd.Series, top_n: int = 5) -> List[Tuple[str, int]]:
    series = series.dropna().astype(str)
    if series.empty:
        return []
    counts = series.value_counts().head(top_n)
    return [(str(idx), int(cnt)) for idx, cnt in counts.items()]


def _estimate_class_imbalance(target_series: pd.Series) -> Optional[Dict[str, Any]]:
    target_series = target_series.dropna()
    if target_series.empty:
        return None
    counts = target_series.astype(str).value_counts()
    if counts.empty:
        return None
    largest = counts.iloc[0]
    return {
        "largest_class": str(counts.index[0]),
        "largest_percent": round(float(largest / counts.sum() * 100), 2),
        "class_count": int(len(counts)),
    }


def _build_observations_insights_for_chart(
    df: pd.DataFrame,
    chart_kind: str,
    title: str,
    target_column: Optional[str] = None,
    chart_cols: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    chart_cols = chart_cols or {}

    observations: List[str] = []
    insights: List[str] = []
    recommendation: str = "Use data-driven preprocessing and validate with cross-validation."  # safe fallback

    # Heatmaps and correlation
    if chart_kind in {"Correlation", "Heatmap"}:
        # Try to infer numeric columns from df
        numeric = df.select_dtypes(include=[np.number])
        if chart_kind == "Heatmap":
            # likely missing-value heatmap in existing charts
            na_counts = df.isna().sum().sort_values(ascending=False)
            top_missing = na_counts[na_counts > 0].head(3)
            if len(top_missing) > 0:
                for col, cnt in top_missing.items():
                    observations.append(f"Missing values are highest in {col} (≈{int(cnt)} missing cells).")
                insights.append("Imputation may be needed, especially for the most-missing columns.")
                recommendation = "Consider targeted imputation (median/mode) and re-check missingness after cleaning."
            else:
                observations.append("No significant missing-value concentration was detected.")
                insights.append("Missingness is unlikely to be a major driver of model instability.")
                recommendation = "Proceed with standard preprocessing (scaling/encoding) and focus on feature quality."
        else:
            if numeric.shape[1] < 2:
                observations.append("Not enough numeric columns exist to compute meaningful correlation patterns.")
            else:
                corr = numeric.corr(numeric_only=True)
                # strongest pair excluding diagonal
                corr_mask = corr.where(~np.eye(corr.shape[0], dtype=bool))
                abs_corr = corr_mask.abs().stack().sort_values(ascending=False)
                if not abs_corr.empty:
                    top = abs_corr.head(1)
                    (pair, strength) = next(iter(top.items()))
                    # pair is (i,j)
                    i, j = pair
                    val = _safe_float(corr.loc[i, j])
                    observations.append(f"Strongest linear relationship is between {i} and {j} (correlation ≈{val:.3f}).")
                    insights.append("Highly correlated features may introduce multicollinearity for linear models.")
                    recommendation = "Consider regularization (e.g., Ridge/Lasso) or feature selection to reduce redundancy."

                # out high-level clustering note
                if corr.shape[0] >= 3:
                    strong_pairs = abs_corr[abs_corr > 0.7]
                    observations.append(f"Approximately {int(strong_pairs.shape[0])} numeric pairs have |correlation| > 0.7 (from sampled columns).")
                    if not strong_pairs.empty:
                        insights.append("Feature redundancy is likely; dimensionality reduction or selection may help generalization.")

    # Histogram
    if chart_kind == "Histogram":
        col = chart_cols.get("col") or _infer_primary_numeric_col_from_title(title)
        if col and col in df.columns and _is_numeric_series(df[col]):
            s = df[col]
            q = _quantiles(s)
            skew = _skewness(s)
            obs_range = (q.get(0.25), q.get(0.75))
            if obs_range[0] is not None and obs_range[1] is not None:
                observations.append(f"Central bulk of values lies between Q1≈{obs_range[0]:.3f} and Q3≈{obs_range[1]:.3f}.")
            if skew is not None:
                direction = "right-skewed" if skew > 0 else "left-skewed" if skew < 0 else "approximately symmetric"
                observations.append(f"Distribution shape appears {direction} (skewness≈{skew:.3f}).")
            outliers = _outlier_count_iqr(s)
            observations.append(f"Outlier presence (IQR rule) ≈ {outliers} extreme values.")

            if skew is not None and abs(skew) > 0.5:
                insights.append("The feature may not be normally distributed; consider robust scaling or transformations.")
            if outliers > 0:
                insights.append("Extreme values could affect distance-based models and regression stability.")
                recommendation = "Try robust scaling (or log/Box-Cox for positive-skew features) and evaluate with/without outlier handling."

    if chart_kind == "Boxplot":
        col = chart_cols.get("col") or _infer_primary_numeric_col_from_title(title)
        if col and col in df.columns and _is_numeric_series(df[col]):
            s = df[col]
            q = _quantiles(s)
            median = q.get(0.5)
            q1 = q.get(0.25)
            q3 = q.get(0.75)
            if median is not None and q1 is not None and q3 is not None:
                observations.append(f"Median≈{median:.3f}; middle 50% spans IQR≈{(q3 - q1):.3f}.")
            outliers = _outlier_count_iqr(s)
            if outliers > 0:
                observations.append(f"Several outliers are detected (IQR rule) ≈ {outliers} points.")
                insights.append("Extreme values exist and may require robust estimators or outlier treatment.")
                recommendation = "Consider winsorization/capping or robust regression; validate impact via cross-validation."
            else:
                observations.append("No major outlier concentration detected by IQR rule.")
                insights.append("The distribution looks relatively stable with respect to extremes.")
                recommendation = "Proceed with scaling/encoding; focus on model selection and feature relevance."

    if chart_kind == "Line":
        col = chart_cols.get("col") or _infer_primary_numeric_col_from_title(title)
        if col and col in df.columns and _is_numeric_series(df[col]):
            s = df[col].dropna()
            if not s.empty:
                q = _quantiles(s)
                obs_range = (q.get(0.05), q.get(0.95))
                if obs_range[0] is not None and obs_range[1] is not None:
                    observations.append(f"Values range from ≈{obs_range[0]:.3f} to ≈{obs_range[1]:.3f} across the sampled order.")
                # basic trend proxy: correlation with index
                idx = np.arange(len(s))
                try:
                    trend = _safe_float(pd.Series(idx).corr(s.reset_index(drop=True)))
                except Exception:
                    trend = None
                if trend is not None:
                    direction = "increasing" if trend > 0 else "decreasing" if trend < 0 else "non-linear/weak"
                    observations.append(f"A simple index-to-value trend signal suggests an {direction} pattern (corr≈{trend:.3f}).")
                    insights.append("If the underlying data is temporal/order-based, trend features may improve predictive models.")
                    recommendation = "If this index represents time, consider time-series feature engineering; otherwise treat order as arbitrary and focus on distributional features."

    if chart_kind == "Scatter":
        x = chart_cols.get("x")
        y = chart_cols.get("y")
        if x and y and x in df.columns and y in df.columns:
            corr = _corr_for_numeric(df, x, y)
            if corr is not None:
                observations.append(f"The two features show a linear association (correlation≈{corr:.3f}).")
                direction = "positive" if corr > 0 else "negative" if corr < 0 else "near-zero"
                observations.append(f"Association direction appears {direction}.")

                strength = abs(corr)
                if strength > 0.7:
                    observations.append("Relationship looks fairly strong for linear modeling.")
                elif strength > 0.3:
                    observations.append("Relationship is moderate; non-linear models may add value.")
                else:
                    observations.append("Relationship is weak; additional features may be needed.")

                insights.append("A regression model (linear or regularized) can be a sensible baseline if linearity holds.")
                recommendation = "Validate with train/test splits; consider robust regression or non-linear learners if residuals show structure."

    if chart_kind == "Target":
        # Feature-vs-target: use kind based on whether target is numeric
        x = chart_cols.get("x") or chart_cols.get("feature")
        y = chart_cols.get("y") or chart_cols.get("target")
        target_series = df[y] if y and y in df.columns else None
        feature_series = df[x] if x and x in df.columns else None

        if x and y and x in df.columns and y in df.columns and _is_numeric_series(df[x]) and _is_numeric_series(df[y]):
            corr = _corr_for_numeric(df, x, y)
            if corr is not None:
                observations.append(f"Feature {x} correlates with target {y} (correlation≈{corr:.3f}).")
                insights.append("This suggests the feature carries predictive signal for the target.")
                recommendation = "Retain the feature (after scaling) and assess using model-based feature importance/ablation."
        elif x and y and x in df.columns and y in df.columns:
            # for categorical target/box: estimate category spread (simple)
            if _is_numeric_series(feature_series) and not _is_numeric_series(target_series):
                means = df.groupby(y)[x].mean().sort_values(ascending=False)
                if not means.empty:
                    top_cat = str(means.index[0])
                    observations.append(f"Target groups differ in {x}; highest group is ≈{top_cat} (mean signal stands out).")
                    insights.append("Group-wise differences indicate category-dependent effects.")
                    recommendation = "Use encoding for categorical target/features and consider tree-based models to capture group effects."

    if chart_kind == "Countplot":
        col = chart_cols.get("col") or _infer_primary_categorical_col_from_title(title)
        if col and col in df.columns:
            counts = df[col].astype(str).value_counts(dropna=False)
            if not counts.empty:
                top = counts.iloc[0]
                observations.append(f"Top category in {col} appears most frequently (count≈{int(top)}).")
                if len(counts) > 1:
                    lowest = counts.iloc[-1]
                    observations.append(f"Least frequent observed category count≈{int(lowest)}.")
                insights.append("There is likely class/category imbalance across groups.")
                recommendation = "If categories are used as features, encode carefully; consider class-balanced sampling or grouped metrics."

    if chart_kind == "Pie":
        # Similar to countplot but can refer to top share
        col = chart_cols.get("col") or _infer_primary_categorical_col_from_title(title)
        if col and col in df.columns:
            counts = df[col].astype(str).value_counts(dropna=False)
            if not counts.empty:
                share = float(counts.iloc[0] / counts.sum() * 100)
                observations.append(f"The most common category in {col} dominates with share≈{share:.2f}%.")
                insights.append("Models may overfit to majority categories if trained directly on raw frequency." )
                recommendation = "Use stratified splits and consider regularization/imbalance-aware objectives when applicable."

    if chart_kind == "Pairplot":
        # pairplot summarizes relationships; focus on highest-correlation pair among sampled numeric columns
        numeric = df.select_dtypes(include=[np.number])
        if numeric.shape[1] >= 2:
            corr = numeric.corr(numeric_only=True)
            abs_corr = corr.where(~np.eye(corr.shape[0], dtype=bool)).abs().stack().sort_values(ascending=False)
            if not abs_corr.empty:
                best_idx = abs_corr.index[0]
                i, j = best_idx
                val = _safe_float(corr.loc[i, j])
                observations.append(f"Pairplot suggests strongest relationship between {i} and {j} (corr≈{val:.3f}).")
                insights.append("Feature pairs with high correlation may benefit from dimensionality reduction or careful regularization." )
                recommendation = "If using linear models, consider regularization; for non-linear models, ensure enough capacity and robust validation." 

    # If nothing was added, fallback generic text based on available computed stats.
    if not observations:
        # general distribution note
        numeric = df.select_dtypes(include=[np.number])
        if not numeric.empty:
            obs = numeric.median(numeric_only=True).iloc[0] if numeric.shape[1] else None
            observations.append("The dataset contains numeric and/or categorical features; inspect distributions and relationships per chart type.")
            insights.append("Use cross-validation to confirm whether visible patterns translate into predictive signal.")
            recommendation = "Apply standard preprocessing (imputation, encoding, scaling) and evaluate with model-based metrics."
        else:
            observations.append("Insufficient numeric data to compute rich statistical insights for this chart.")
            insights.append("Consider preprocessing to extract numeric signals or confirm feature types.")
            recommendation = "Re-check column types and consider feature engineering/encoding." 

    return {
        "observations": observations[:3],
        "key_insights": insights[:3],
        "recommendation": recommendation,
    }


def _infer_primary_numeric_col_from_title(title: str) -> Optional[str]:
    # Titles are like "Histogram: col" or "Boxplot: col" or "Line Chart: col".
    if ":" not in title:
        return None
    try:
        kind, col = title.split(":", 1)
    except ValueError:
        return None
    return col.strip() if col.strip() else None


def _infer_primary_categorical_col_from_title(title: str) -> Optional[str]:
    # Titles like "Countplot: col" or "Pie Chart: col"
    if ":" not in title:
        return None
    parts = title.split(":", 1)
    if len(parts) != 2:
        return None
    return parts[1].strip() if parts[1].strip() else None

