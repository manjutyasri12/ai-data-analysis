from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _div(fig) -> str:
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=30, r=24, t=58, b=34),
        height=430,
    )
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})


def smart_charts(df: pd.DataFrame, target_column: Optional[str] = None) -> List[Dict[str, Any]]:
    charts: List[Dict[str, Any]] = []
    sample = df.head(1000).copy()
    numeric = sample.select_dtypes(include=[np.number]).columns.tolist()
    categorical = [c for c in sample.columns if c not in numeric]

    missing_matrix = sample.isna().astype(int)
    if not missing_matrix.empty:
        charts.append(
            {
                "title": "Dataset Missing-Value Heatmap",
                "kind": "Heatmap",
                "html": _div(px.imshow(missing_matrix.T, aspect="auto", color_continuous_scale="Blues")),
            }
        )

    if len(numeric) >= 2:
        corr = sample[numeric].corr(numeric_only=True).round(3)
        charts.append(
            {
                "title": "Correlation Heatmap",
                "kind": "Correlation",
                "html": _div(px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1)),
            }
        )
    else:
        fig = go.Figure()
        fig.add_annotation(text="At least two numeric columns are needed for correlation.", showarrow=False)
        charts.append({"title": "Correlation Heatmap", "kind": "Correlation", "html": _div(fig)})

    for col in numeric[:4]:
        charts.append({"title": f"Histogram: {col}", "kind": "Histogram", "html": _div(px.histogram(sample, x=col, nbins=30))})
        charts.append({"title": f"Boxplot: {col}", "kind": "Boxplot", "html": _div(px.box(sample, y=col))})
        charts.append({"title": f"Line Chart: {col}", "kind": "Line", "html": _div(px.line(sample.reset_index(), x="index", y=col))})

    if len(numeric) >= 2:
        charts.append(
            {
                "title": f"Scatterplot: {numeric[0]} vs {numeric[1]}",
                "kind": "Scatter",
                "html": _div(px.scatter(sample, x=numeric[0], y=numeric[1], color=target_column if target_column in sample.columns else None)),
            }
        )

    for col in categorical[:4]:
        counts = sample[col].astype(str).value_counts().head(15).reset_index()
        counts.columns = [col, "count"]
        charts.append({"title": f"Countplot: {col}", "kind": "Countplot", "html": _div(px.bar(counts, x=col, y="count"))})
        charts.append({"title": f"Pie Chart: {col}", "kind": "Pie", "html": _div(px.pie(counts, names=col, values="count"))})

    if target_column and target_column in sample.columns:
        target_is_numeric = target_column in numeric
        for col in [c for c in numeric if c != target_column][:4]:
            if target_is_numeric:
                charts.append(
                    {
                        "title": f"Feature vs Target: {col} vs {target_column}",
                        "kind": "Target",
                        "html": _div(px.scatter(sample, x=col, y=target_column, trendline="ols")),
                    }
                )
            else:
                charts.append(
                    {
                        "title": f"Feature vs Target: {col} by {target_column}",
                        "kind": "Target",
                        "html": _div(px.box(sample, x=target_column, y=col)),
                    }
                )
        pair_cols = [c for c in numeric if c != target_column][:4]
        if target_is_numeric:
            pair_cols = (pair_cols + [target_column])[:5]
        if len(pair_cols) >= 2:
            charts.append(
                {
                    "title": "Pairplot",
                    "kind": "Pairplot",
                    "html": _div(px.scatter_matrix(sample, dimensions=pair_cols, color=target_column if not target_is_numeric else None)),
                }
            )

    return charts
