import json
import logging
import os
import time
import uuid
import warnings
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from django.conf import settings
from dotenv import load_dotenv

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None

try:
    from google.api_core import exceptions as google_exceptions
except ImportError:  # pragma: no cover
    google_exceptions = None

logger = logging.getLogger(__name__)

GEMINI_MODEL_PREFERRED_ORDER = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-pro",
]

# This will be auto-selected at runtime. Never hardcode a model name.
GEMINI_MODEL = ""
GEMINI_TIMEOUT_SECONDS = 40
GEMINI_MAX_OUTPUT_TOKENS = 2048
GEMINI_RETRY_ATTEMPTS = 2
MAX_CONTEXT_CHARS = 24000
MAX_COLUMNS_IN_DETAIL = 80
MAX_STAT_COLUMNS = 40
MAX_CORRELATIONS = 25
MAX_MODEL_ROWS = 30
MAX_PREDICTION_ROWS = 20


class GeminiAssistantError(Exception):
    status = "gemini_unavailable"
    user_message = "Gemini is unavailable right now. Please try again shortly."


class MissingApiKeyError(GeminiAssistantError):
    status = "missing_api_key"
    user_message = "Gemini API key is missing. Add GEMINI_API_KEY to your .env file."


class InvalidApiKeyError(GeminiAssistantError):
    status = "invalid_api_key"
    user_message = "Gemini API key is invalid. Check GEMINI_API_KEY in your .env file."


class GeminiQuotaError(GeminiAssistantError):
    status = "quota_exceeded"
    user_message = "Gemini quota exceeded. Please wait or check your Google AI billing/quota."


class GeminiTimeoutError(GeminiAssistantError):
    status = "timeout"
    user_message = "Gemini took too long to respond. Try a shorter question."


class GeminiPackageError(GeminiAssistantError):
    status = "package_missing"
    user_message = "Gemini package is unavailable. Install google-generativeai."


class EmptyResponseError(GeminiAssistantError):
    status = "empty_response"
    user_message = "Gemini returned an empty response. Please try again."


class IncompleteResponseError(GeminiAssistantError):
    status = "incomplete_response"
    user_message = "Gemini stopped before completing the answer. Please ask a narrower question."


def _load_env() -> bool:
    env_path = settings.BASE_DIR / ".env"
    loaded = load_dotenv(env_path, override=False)
    logger.debug("Gemini dotenv load attempted. path=%s loaded=%s exists=%s", env_path, loaded, env_path.exists())
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


def _result(success: bool, message: str, status: str = "ok", **extra: Any) -> Dict[str, Any]:
    payload = {
        "success": success,
        "status": status,
        "response": message,
        "answer": message if success else "",
        "error": "" if success else message,
    }
    payload.update(extra)
    return payload


def _safe_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        if np.isnan(value) or np.isinf(value):
            return None
        return round(float(value), 6)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _json(value: Any, indent: Optional[int] = 2) -> str:
    return json.dumps(value, ensure_ascii=True, default=str, indent=indent)


def _truncate_text(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[:max_chars] + "\n[Context truncated to keep the Gemini request stable.]"


def _discover_available_gemini_models() -> List[str]:
    """Return fully-qualified model names as exposed by genai.list_models()."""
    if genai is None:
        return []

    # Ensure configured
    validation = validate_gemini_setup()
    if not validation.get("api_key_loaded"):
        return []

    try:
        return [m.name for m in genai.list_models()]
    except Exception:
        return []


def _extract_supported_generation_methods(model_obj: Any) -> List[str]:
    for attr in [
        "supported_generation_methods",
        "supportedGenerationMethods",
    ]:
        val = getattr(model_obj, attr, None)
        if isinstance(val, list):
            return [str(x) for x in val]
    capabilities = getattr(model_obj, "capabilities", None)
    if isinstance(capabilities, dict):
        val = capabilities.get("supported_generation_methods") or capabilities.get("supportedGenerationMethods")
        if isinstance(val, list):
            return [str(x) for x in val]
    return []


def _short_to_fqn(short_name: str) -> List[str]:
    """Map short names to the set of possible fully-qualified names."""
    # Observed naming from list_models(): models/<short>
    candidates = [f"models/{short_name}"]

    # Also allow '-latest' style matches for 'gemini-flash-latest' when short_name is 'gemini-flash-latest'
    # (we only use this for the preferred order that doesn't include latest suffixes).
    return candidates


def get_best_available_model() -> Dict[str, Any]:
    """Auto-select first preferred model that exists and supports generateContent.

    Returns dict with:
      - selected_model (fully-qualified)
      - attempted_models (list)
      - failed_models (list of {model,error,status})
      - available_models_count
    """
    started = time.perf_counter()

    available_models: List[str] = _discover_available_gemini_models()
    available_set = set(available_models)

    # If discovery isn't possible, still fall back to best-effort preferred mapping.
    attempted: List[str] = []
    failed: List[Dict[str, Any]] = []

    # Build candidate fully-qualified models in your preferred order.
    candidates: List[str] = []
    for short in GEMINI_MODEL_PREFERRED_ORDER:
        candidates.extend(_short_to_fqn(short))

    # De-dup while preserving order
    seen = set()
    ordered_candidates: List[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            ordered_candidates.append(c)

    # To check capabilities, we need model objects, not just names.
    # list_models() returns objects; re-run to also capture capabilities.
    model_objects = []
    if genai is not None and available_models:
        try:
            model_objects = list(genai.list_models())
        except Exception:
            model_objects = []

    obj_by_name = {getattr(o, "name", None): o for o in model_objects if getattr(o, "name", None)}

    for fqn in ordered_candidates:
        attempted.append(fqn)
        if available_models and fqn not in available_set:
            continue

        mobj = obj_by_name.get(fqn)
        if mobj is None:
            # If we didn't get the object (capability introspection failed), assume generateContent is supported
            # because the API would otherwise 404/400 quickly.
            return {
                "selected_model": fqn,
                "attempted_models": attempted,
                "failed_models": failed,
                "available_models_count": len(available_models),
                "selection_elapsed_seconds": round(time.perf_counter() - started, 3),
            }

        methods = _extract_supported_generation_methods(mobj)
        if "generateContent" in methods:
            return {
                "selected_model": fqn,
                "attempted_models": attempted,
                "failed_models": failed,
                "available_models_count": len(available_models),
                "selection_elapsed_seconds": round(time.perf_counter() - started, 3),
            }

        # Capability mismatch, mark as failed and try next
        failed.append({"model": fqn, "error": "generateContent not supported", "status": "capability_mismatch"})

    return {
        "selected_model": "",
        "attempted_models": attempted,
        "failed_models": failed,
        "available_models_count": len(available_models),
        "selection_elapsed_seconds": round(time.perf_counter() - started, 3),
    }


def validate_gemini_setup() -> Dict[str, Any]:
    has_key = _load_env()
    package_ok = genai is not None
    # Model will be selected dynamically; keep legacy field for diagnostics
    model_name = GEMINI_MODEL
    configured = False

    if not package_ok:
        return {
            "package_installed": False,
            "dotenv_loaded": has_key,
            "api_key_loaded": has_key,
            "model": model_name,
            "configured": False,
            "status": "package_missing",
        }
    if not has_key:
        return {
            "package_installed": True,
            "dotenv_loaded": False,
            "api_key_loaded": False,
            "model": model_name,
            "configured": False,
            "status": "missing_api_key",
        }

    genai.configure(api_key=os.getenv("GEMINI_API_KEY", "").strip())
    configured = True
    return {
        "package_installed": package_ok,
        "dotenv_loaded": has_key,
        "api_key_loaded": has_key,
        "model": model_name,
        "configured": configured,
        "status": "ok",
    }


def _configure_gemini() -> None:
    validation = validate_gemini_setup()
    if not validation["package_installed"]:
        raise GeminiPackageError("google-generativeai is not installed.")
    if not validation["api_key_loaded"]:
        raise MissingApiKeyError("GEMINI_API_KEY is missing.")


def _classify_error(exc: Exception) -> GeminiAssistantError:
    if isinstance(exc, GeminiAssistantError):
        return exc

    lowered = str(exc).lower()
    if google_exceptions:
        if isinstance(exc, (google_exceptions.Unauthenticated, google_exceptions.PermissionDenied)):
            return InvalidApiKeyError(str(exc))
        if isinstance(exc, google_exceptions.ResourceExhausted):
            return GeminiQuotaError(str(exc))
        if isinstance(exc, (google_exceptions.DeadlineExceeded, google_exceptions.RetryError)):
            return GeminiTimeoutError(str(exc))
    if "api key" in lowered or "unauthenticated" in lowered or "permission denied" in lowered:
        return InvalidApiKeyError(str(exc))
    if "quota" in lowered or "rate limit" in lowered or "resource_exhausted" in lowered:
        return GeminiQuotaError(str(exc))
    if "timeout" in lowered or "deadline" in lowered:
        return GeminiTimeoutError(str(exc))
    if "finish_reason" in lowered or "max_tokens" in lowered:
        return IncompleteResponseError(str(exc))
    return GeminiAssistantError(str(exc))


def _statistics_context(df: pd.DataFrame) -> Dict[str, Any]:
    numeric = df.select_dtypes(include=[np.number])
    stats: Dict[str, Dict[str, Any]] = {}
    describe = numeric.describe().T if not numeric.empty else pd.DataFrame()

    for column in numeric.columns[:MAX_STAT_COLUMNS]:
        series = numeric[column].dropna()
        if series.empty:
            continue
        mode = series.mode()
        stats[column] = {
            "count": int(series.count()),
            "mean": _safe_value(series.mean()),
            "median": _safe_value(series.median()),
            "mode": _safe_value(mode.iloc[0]) if not mode.empty else None,
            "std": _safe_value(series.std()) if len(series) > 1 else None,
            "variance": _safe_value(series.var()) if len(series) > 1 else None,
            "min": _safe_value(series.min()),
            "q1": _safe_value(series.quantile(0.25)),
            "q3": _safe_value(series.quantile(0.75)),
            "max": _safe_value(series.max()),
            "skewness": _safe_value(series.skew()) if len(series) > 2 else None,
            "kurtosis": _safe_value(series.kurtosis()) if len(series) > 3 else None,
        }

    return {
        "available": bool(stats),
        "numeric_statistics": stats,
        "describe": describe.head(MAX_STAT_COLUMNS).applymap(_safe_value).to_dict("index") if not describe.empty else {},
    }


def _correlation_context(df: pd.DataFrame, target_column: Optional[str] = None) -> Dict[str, Any]:
    numeric = df.select_dtypes(include=[np.number])
    if len(numeric.columns) < 2:
        return {"available": False, "message": "Fewer than two numeric columns are available."}

    corr = numeric.corr(numeric_only=True)
    pairs = []
    for index, column in enumerate(corr.columns):
        for other in corr.columns[index + 1 :]:
            value = corr.at[column, other]
            if not pd.isna(value):
                pairs.append((column, other, float(value)))
    pairs.sort(key=lambda item: abs(item[2]), reverse=True)

    target_correlations = []
    if target_column and target_column in corr.columns:
        target_series = corr[target_column].drop(labels=[target_column], errors="ignore")
        target_correlations = [
            {"feature": feature, "correlation": _safe_value(value)}
            for feature, value in target_series.sort_values(key=lambda s: s.abs(), ascending=False).head(MAX_CORRELATIONS).items()
            if not pd.isna(value)
        ]

    return {
        "available": True,
        "top_pairs": [
            {"columns": [left, right], "correlation": _safe_value(value), "strength": abs(round(value, 6))}
            for left, right, value in pairs[:MAX_CORRELATIONS]
        ],
        "target_correlations": target_correlations,
    }


def _preprocessing_context(report: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    report = report or {}
    label_encodings = report.get("label_encodings", [])
    return {
        "cleaning_summary": report.get("summary", []),
        "missing_value_handling": report.get("missing_values", []),
        "duplicates_removed": int(report.get("duplicates_removed") or 0),
        "encoding_summary": [
            {
                "column": item.get("column"),
                "category_count": len(item.get("mapping", {}) or {}),
                "mapping_sample": dict(list((item.get("mapping", {}) or {}).items())[:10]),
            }
            for item in label_encodings[:MAX_COLUMNS_IN_DETAIL]
        ],
        "outlier_handling": report.get("outliers", []),
        "scaling_summary": report.get("scaling") or "Feature scaling is applied inside the ML pipeline where needed.",
        "preprocessing_summary": report,
    }


def _model_metric_row(row: Dict[str, Any]) -> Dict[str, Any]:
    rmse = _safe_value(row.get("rmse"))
    mse = _safe_value(row.get("mse"))
    if mse is None and rmse is not None:
        mse = _safe_value(float(rmse) ** 2)
    return {
        "model_name": row.get("model_name") or row.get("model") or "Unknown model",
        "status": row.get("status"),
        "accuracy": _safe_value(row.get("accuracy")),
        "precision": _safe_value(row.get("precision")),
        "recall": _safe_value(row.get("recall")),
        "f1_score": _safe_value(row.get("f1_score")),
        "r2": _safe_value(row.get("r2_score", row.get("r2"))),
        "mae": _safe_value(row.get("mae")),
        "mse": mse,
        "rmse": rmse,
        "cv_score": _safe_value(row.get("cv_score")),
        "training_time": _safe_value(row.get("training_time")),
        "error": row.get("error") or "",
    }


def _model_results_context(
    model_comparison_results: Optional[List[Dict[str, Any]]],
    best_model: Optional[str],
    accuracy: Optional[float],
    target_column: Optional[str],
) -> Dict[str, Any]:
    rows = [_model_metric_row(row) for row in (model_comparison_results or [])[:MAX_MODEL_ROWS]]
    successful = [row for row in rows if row.get("status") in {"success", "tested", None} and (row.get("accuracy") is not None or row.get("r2") is not None)]
    if not best_model and successful:
        best = max(successful, key=lambda row: row.get("accuracy") if row.get("accuracy") is not None else row.get("r2") or -999999)
        best_model = best.get("model_name")
        accuracy = accuracy if accuracy is not None else best.get("accuracy") or best.get("r2")

    return {
        "available": bool(rows),
        "target_column": target_column or "Not selected",
        "best_model": best_model or "Not trained yet",
        "best_score": _safe_value(accuracy),
        "all_model_metrics": rows,
        "missing_models_message": "" if rows else "No model comparison results are available yet.",
    }


def _prediction_context(prediction_results: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    rows = prediction_results or []
    return {
        "available": bool(rows),
        "recent_predictions": rows[:MAX_PREDICTION_ROWS],
        "missing_predictions_message": "" if rows else "No prediction results are available yet.",
    }


def build_dataset_context(
    df: pd.DataFrame,
    dataset_name: str = "uploaded dataset",
    target_column: Optional[str] = None,
    preprocessing_report: Optional[Dict[str, Any]] = None,
    model_comparison_results: Optional[List[Dict[str, Any]]] = None,
    best_model: Optional[str] = None,
    accuracy: Optional[float] = None,
    prediction_results: Optional[List[Dict[str, Any]]] = None,
    chart_results: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    column_names = df.columns.tolist()
    missing_values = {column: int(df[column].isna().sum()) for column in column_names}
    target = target_column if target_column in column_names else None
    statistics = _statistics_context(df)
    correlations = _correlation_context(df, target)
    model_results = _model_results_context(model_comparison_results, best_model, accuracy, target)

    context = {
        "dataset_information": {
            "dataset_name": dataset_name,
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "column_names": column_names[:MAX_COLUMNS_IN_DETAIL],
            "total_column_count": len(column_names),
            "data_types": {column: str(df[column].dtype) for column in column_names[:MAX_COLUMNS_IN_DETAIL]},
            "missing_values": missing_values,
            "duplicate_rows": int(df.duplicated().sum()),
            "numeric_columns": numeric_columns[:MAX_COLUMNS_IN_DETAIL],
            "categorical_columns": [column for column in column_names if column not in numeric_columns][:MAX_COLUMNS_IN_DETAIL],
            "target_column": target or "Not selected",
        },
        "statistics": statistics,
        "correlation_results": correlations,
        "visualization_results": {
            "available": bool(chart_results),
            "charts": [
                {
                    "title": chart.get("title"),
                    "kind": chart.get("kind"),
                    "x": chart.get("x"),
                    "y": chart.get("y"),
                }
                for chart in (chart_results or [])[:20]
            ],
            "heatmap_note": "Use correlation_results to explain heatmaps and relationships between numeric columns.",
        },
        "preprocessing": _preprocessing_context(preprocessing_report),
        "model_results": model_results,
        "prediction_results": _prediction_context(prediction_results),
        "context_quality": {
            "has_statistics": statistics["available"],
            "has_correlations": correlations["available"],
            "has_models": model_results["available"],
            "has_predictions": bool(prediction_results),
        },
    }
    logger.info(
        "Gemini dataset context generated. dataset=%s rows=%s columns=%s target=%s stats=%s models=%s predictions=%s",
        dataset_name,
        df.shape[0],
        df.shape[1],
        target or "Not selected",
        statistics["available"],
        model_results["available"],
        bool(prediction_results),
    )
    return context


def build_prompt(question: str, dataset_context: Dict[str, Any]) -> str:
    question = (question or "").strip()
    dataset_info = dataset_context.get("dataset_information", {})
    statistics = dataset_context.get("statistics", {})
    correlations = dataset_context.get("correlation_results", {})
    model_results = dataset_context.get("model_results", {})
    predictions = dataset_context.get("prediction_results", {})
    preprocessing = dataset_context.get("preprocessing", {})
    visualizations = dataset_context.get("visualization_results", {})

    prompt = (
        "You are an expert Data Scientist.\n\n"
        "Rules:\n"
        "1. Answer ONLY using available dataset information whenever possible.\n"
        "2. If a requested statistic, chart, model, or prediction is missing, say exactly what is missing and what the user should run/upload next.\n"
        "3. Do not invent columns, metrics, model results, charts, predictions, or dataset facts.\n"
        "4. Be practical, concise, and dataset-specific.\n"
        "5. For model recommendations, compare the supplied metrics and explain the best model using those metrics.\n"
        "6. For heatmaps, use correlation_results and explain strongest relationships.\n\n"
        "Dataset Information:\n"
        f"{_json(dataset_info)}\n\n"
        "Statistics:\n"
        f"{_json(statistics)}\n\n"
        "Correlation Results:\n"
        f"{_json(correlations)}\n\n"
        "Charts and Heatmaps:\n"
        f"{_json(visualizations)}\n\n"
        "Cleaning, Encoding, and Preprocessing Summary:\n"
        f"{_json(preprocessing)}\n\n"
        "Model Results:\n"
        f"{_json(model_results)}\n\n"
        "Predictions:\n"
        f"{_json(predictions)}\n\n"
        "User Question:\n"
        f"{question}\n\n"
        "Provide practical recommendations and explain your reasoning from the supplied context."
    )
    prompt = _truncate_text(prompt, MAX_CONTEXT_CHARS)
    logger.info("Gemini prompt generated. question_length=%s prompt_chars=%s", len(question), len(prompt))
    logger.debug("Gemini prompt preview: %s", prompt[:1200])
    return prompt


def _candidate_finish_reason(response: Any) -> str:
    candidates = getattr(response, "candidates", []) or []
    if not candidates:
        return ""
    reason = getattr(candidates[0], "finish_reason", "")
    return str(reason or "")


def _extract_text(response: Any) -> str:
    try:
        text = getattr(response, "text", None)
        if text:
            return str(text).strip()
    except Exception:
        pass

    chunks: List[str] = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            part_text = getattr(part, "text", None)
            if part_text:
                chunks.append(str(part_text))
    return "\n".join(chunks).strip()


def _needs_retry(exc: GeminiAssistantError) -> bool:
    return exc.status in {"timeout", "gemini_unavailable", "empty_response", "incomplete_response"}


def _generate_once(prompt: str, request_id: str, model_name: str) -> Dict[str, Any]:
    model = genai.GenerativeModel(
        model_name,
        generation_config={
            "temperature": 0.15,
            "top_p": 0.85,
            "top_k": 40,
            "max_output_tokens": GEMINI_MAX_OUTPUT_TOKENS,
        },
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
    )
    response = model.generate_content(prompt, request_options={"timeout": GEMINI_TIMEOUT_SECONDS})
    finish_reason = _candidate_finish_reason(response)
    answer = _extract_text(response)
    logger.info(
        "Gemini API response received. request_id=%s answer_chars=%s finish_reason=%s",
        request_id,
        len(answer),
        finish_reason or "unknown",
    )
    logger.debug("Gemini response preview. request_id=%s preview=%s", request_id, answer[:1200])

    if not answer:
        raise EmptyResponseError("Gemini returned no text.")
    if "MAX_TOKENS" in finish_reason.upper():
        raise IncompleteResponseError("Gemini stopped because the output token limit was reached.")
    return {"answer": answer, "finish_reason": finish_reason or "unknown"}


def ask_gemini(question: str, dataset_context: Dict[str, Any]) -> Dict[str, Any]:
    request_id = uuid.uuid4().hex[:10]
    question = (question or "").strip()
    if not question:
        return _result(False, "Please type a question before asking Gemini.", "empty_question", request_id=request_id)
    if not dataset_context:
        return _result(False, "Dataset not loaded. Please upload a CSV dataset first.", "dataset_not_loaded", request_id=request_id)

    started = time.perf_counter()
    logger.info("Gemini API request started. request_id=%s question_chars=%s", request_id, len(question))

    try:
        _configure_gemini()
        prompt = build_prompt(question, dataset_context)

        selection = get_best_available_model()
        selected_model = selection.get("selected_model", "")

        preferred_candidates: List[str] = []
        for short in GEMINI_MODEL_PREFERRED_ORDER:
            preferred_candidates.extend(_short_to_fqn(short))
        # de-dup
        seen = set()
        fallback_models: List[str] = []
        for m in preferred_candidates:
            if m not in seen:
                seen.add(m)
                fallback_models.append(m)

        if selected_model and selected_model in fallback_models:
            fallback_models = [selected_model] + [m for m in fallback_models if m != selected_model]

        logger.info(
            "Gemini model selected. selected_model=%s attempted=%s available_models_count=%s",
            selected_model,
            selection.get("attempted_models"),
            selection.get("available_models_count"),
        )

        if not selected_model:
            raise GeminiAssistantError("No compatible Gemini model found. Check API access/quota.")

        last_error: Optional[GeminiAssistantError] = None

        for model_index, model_name in enumerate(fallback_models, start=1):
            for attempt in range(1, GEMINI_RETRY_ATTEMPTS + 1):
                try:
                    t0 = time.perf_counter()
                    logger.info(
                        "Gemini API attempt. request_id=%s model_index=%s attempt=%s model=%s",
                        request_id,
                        model_index,
                        attempt,
                        model_name,
                    )
                    generated = _generate_once(prompt, request_id, model_name=model_name)
                    elapsed = round(time.perf_counter() - started, 3)
                    api_time = round(time.perf_counter() - t0, 3)
                    return _result(
                        True,
                        generated["answer"],
                        "ok",
                        request_id=request_id,
                        finish_reason=generated["finish_reason"],
                        elapsed_seconds=elapsed,
                        model_name=model_name,
                        api_time_seconds=api_time,
                    )
                except Exception as exc:
                    classified = _classify_error(exc)
                    last_error = classified
                    logger.warning(
                        "Gemini API attempt failed. request_id=%s model=%s attempt=%s status=%s error=%s",
                        request_id,
                        model_name,
                        attempt,
                        classified.status,
                        str(exc),
                    )

                    if attempt >= GEMINI_RETRY_ATTEMPTS or not _needs_retry(classified):
                        break

        raise last_error or GeminiAssistantError("Gemini request failed.")
    except Exception as exc:
        classified = _classify_error(exc)
        logger.exception("Gemini request failed. request_id=%s status=%s", request_id, classified.status)
        return _result(False, classified.user_message, classified.status, request_id=request_id)


def run_diagnostics(sample_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    checks: Dict[str, Any] = {
        "api_connectivity": False,
        "dataset_context": bool(sample_context),
        "prompt_generation": False,
        "response_generation": False,
        "error_handling": False,
    }
    validation = validate_gemini_setup()
    checks["validation"] = validation

    try:
        if sample_context:
            prompt = build_prompt("Explain this dataset in one sentence.", sample_context)
            checks["prompt_generation"] = bool(prompt and "Dataset Information:" in prompt and "Model Results:" in prompt)
            checks["prompt_chars"] = len(prompt)
        _configure_gemini()
        selection = get_best_available_model()
        model_name = selection.get("selected_model") or GEMINI_MODEL or ""
        if not model_name:
            raise GeminiAssistantError("No compatible Gemini model found for diagnostics.")
        model = genai.GenerativeModel(model_name, generation_config={"temperature": 0, "max_output_tokens": 40})
        response = model.generate_content(
            "Reply exactly with: Gemini working successfully",
            request_options={"timeout": GEMINI_TIMEOUT_SECONDS},
        )
        answer = _extract_text(response)
        checks["api_connectivity"] = "Gemini working successfully" in answer
        checks["response_generation"] = bool(answer)
        checks["response"] = answer
    except Exception as exc:
        classified = _classify_error(exc)
        checks["error_handling"] = True
        checks["error_status"] = classified.status
        checks["error_message"] = classified.user_message
        logger.exception("Gemini diagnostics failed. status=%s", classified.status)
        return _result(False, classified.user_message, classified.status, checks=checks)

    checks["error_handling"] = True
    success = checks["api_connectivity"] and checks["prompt_generation"] if sample_context else checks["api_connectivity"]
    message = "Gemini working successfully" if success else "Gemini diagnostics completed with warnings."
    return _result(success, message, "ok" if success else "diagnostic_warning", checks=checks)


def test_gemini_connection() -> Dict[str, Any]:
    return run_diagnostics()


# ============================================================
# REPORT GENERATION & ADVANCED FEATURES
# ============================================================

def _build_executive_summary_prompt(dataset_context: Dict[str, Any]) -> str:
    """Build prompt for executive summary generation"""
    dataset_info = dataset_context.get("dataset_information", {})
    model_results = dataset_context.get("model_results", {})
    
    prompt = (
        "Generate a concise executive summary (150-200 words) for a dataset analysis project.\n\n"
        f"Dataset: {dataset_info.get('dataset_name')}\n"
        f"Rows: {dataset_info.get('rows')}\n"
        f"Columns: {dataset_info.get('columns')}\n"
        f"Target: {dataset_info.get('target_column')}\n"
        f"Best Model: {model_results.get('best_model')}\n"
        f"Accuracy: {model_results.get('best_score')}\n\n"
        "Include: Data overview, preprocessing approach, model selection rationale, and key findings. "
        "Be professional and business-focused."
    )
    return prompt


def _build_insights_prompt(dataset_context: Dict[str, Any]) -> str:
    """Build prompt for business insights generation"""
    correlations = dataset_context.get("correlation_results", {})
    statistics = dataset_context.get("statistics", {})
    model_results = dataset_context.get("model_results", {})
    
    prompt = (
        "Analyze the provided dataset and generate 5-7 key business insights.\n\n"
        "Top Correlations:\n"
        f"{_json(correlations.get('top_pairs', [])[:5])}\n\n"
        "Statistics Available: Statistics enabled for numeric columns.\n\n"
        "Model Performance:\n"
        f"{_json(model_results.get('all_model_metrics', [])[:5])}\n\n"
        "Format each insight as:\n"
        "- **Insight Title**: Explanation with numbers and recommendations.\n\n"
        "Focus on actionable insights that drive decision-making."
    )
    return prompt


def _build_research_paper_prompt(dataset_context: Dict[str, Any]) -> str:
    """Build prompt for research paper content generation"""
    dataset_info = dataset_context.get("dataset_information", {})
    model_results = dataset_context.get("model_results", {})
    preprocessing = dataset_context.get("preprocessing", {})
    
    prompt = (
        "Generate academic research paper sections based on this machine learning project.\n\n"
        "SECTIONS TO INCLUDE:\n"
        "1. **Abstract** (150-200 words)\n"
        "2. **Introduction** (Dataset overview, problem statement)\n"
        "3. **Methodology** (Data preprocessing, feature engineering, model selection)\n"
        "4. **Results** (Performance metrics, model comparison)\n"
        "5. **Discussion** (Findings, limitations, future work)\n\n"
        f"Dataset: {dataset_info.get('dataset_name')} ({dataset_info.get('rows')} rows, {dataset_info.get('columns')} columns)\n"
        f"Target: {dataset_info.get('target_column')}\n"
        f"Best Model: {model_results.get('best_model')} (Accuracy: {model_results.get('best_score')})\n"
        f"Preprocessing: {len(preprocessing.get('encoding_summary', []))} encoded features\n\n"
        "Use formal academic language, cite preprocessing techniques, and discuss model choices."
    )
    return prompt


def generate_executive_summary(dataset_context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate executive summary of dataset analysis"""
    request_id = uuid.uuid4().hex[:10]
    logger.info("Executive summary generation started. request_id=%s", request_id)
    
    try:
        _configure_gemini()
        prompt = _build_executive_summary_prompt(dataset_context)
        prompt = _truncate_text(prompt, MAX_CONTEXT_CHARS)
        generated = _generate_once(prompt, request_id)
        return _result(True, generated["answer"], "ok", request_id=request_id, summary_type="executive")
    except Exception as exc:
        classified = _classify_error(exc)
        logger.exception("Executive summary generation failed. request_id=%s status=%s", request_id, classified.status)
        return _result(False, classified.user_message, classified.status, request_id=request_id)


def generate_business_insights(dataset_context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate actionable business insights from dataset"""
    request_id = uuid.uuid4().hex[:10]
    logger.info("Business insights generation started. request_id=%s", request_id)
    
    try:
        _configure_gemini()
        prompt = _build_insights_prompt(dataset_context)
        prompt = _truncate_text(prompt, MAX_CONTEXT_CHARS)
        generated = _generate_once(prompt, request_id)
        return _result(True, generated["answer"], "ok", request_id=request_id, insights_type="business")
    except Exception as exc:
        classified = _classify_error(exc)
        logger.exception("Business insights generation failed. request_id=%s status=%s", request_id, classified.status)
        return _result(False, classified.user_message, classified.status, request_id=request_id)


def generate_research_paper(dataset_context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate research paper content from ML project"""
    request_id = uuid.uuid4().hex[:10]
    logger.info("Research paper generation started. request_id=%s", request_id)
    
    try:
        _configure_gemini()
        prompt = _build_research_paper_prompt(dataset_context)
        prompt = _truncate_text(prompt, MAX_CONTEXT_CHARS)
        generated = _generate_once(prompt, request_id)
        return _result(True, generated["answer"], "ok", request_id=request_id, paper_type="research")
    except Exception as exc:
        classified = _classify_error(exc)
        logger.exception("Research paper generation failed. request_id=%s status=%s", request_id, classified.status)
        return _result(False, classified.user_message, classified.status, request_id=request_id)


def analyze_entire_dataset(df: pd.DataFrame, target_column: Optional[str] = None) -> Dict[str, Any]:
    """Perform comprehensive AI analysis of entire dataset"""
    request_id = uuid.uuid4().hex[:10]
    logger.info("Full dataset analysis started. request_id=%s rows=%s columns=%s", request_id, df.shape[0], df.shape[1])
    
    try:
        # Build complete context
        context = build_dataset_context(df, target_column=target_column)
        
        # Create comprehensive analysis prompt
        prompt = (
            "Perform a comprehensive analysis of this dataset.\n\n"
            "Provide:\n"
            "1. **Dataset Type**: Classification/Regression/Other\n"
            "2. **Data Quality Score**: 0-100\n"
            "3. **Recommended ML Task**: What problem this dataset is best suited for\n"
            "4. **Feature Importance Ranking**: Top 5 most important features\n"
            "5. **Target Column Suggestions**: If target not specified, recommend what to predict\n"
            "6. **Recommended Models**: 3-5 models suited for this task\n"
            "7. **Potential Issues**: Data imbalance, missing values, outliers, etc.\n"
            "8. **Recommended Cleaning Steps**: Specific actions to improve data quality\n"
            "9. **Feature Engineering Ideas**: Specific new features to create\n"
            "10. **Success Metrics**: Best metrics to track model performance\n\n"
            f"Dataset Context:\n{_json(context)}\n\n"
            "Be specific with recommendations based on the provided data."
        )
        
        _configure_gemini()
        prompt = _truncate_text(prompt, MAX_CONTEXT_CHARS)
        generated = _generate_once(prompt, request_id)
        
        return _result(
            True, 
            generated["answer"], 
            "ok", 
            request_id=request_id,
            analysis_type="comprehensive",
            rows_analyzed=int(df.shape[0]),
            columns_analyzed=int(df.shape[1])
        )
    except Exception as exc:
        classified = _classify_error(exc)
        logger.exception("Full dataset analysis failed. request_id=%s status=%s", request_id, classified.status)
        return _result(False, classified.user_message, classified.status, request_id=request_id)


def explain_model_comparison(model_results: List[Dict[str, Any]], best_model: str) -> Dict[str, Any]:
    """Explain why best model performed better than others"""
    request_id = uuid.uuid4().hex[:10]
    logger.info("Model comparison explanation started. request_id=%s models=%s best=%s", request_id, len(model_results), best_model)
    
    try:
        _configure_gemini()
        
        prompt = (
            "Compare these machine learning models and explain performance differences.\n\n"
            f"Model Leaderboard:\n{_json(model_results[:MAX_MODEL_ROWS])}\n\n"
            f"Best Model: {best_model}\n\n"
            "Answer these questions:\n"
            "1. Why did the best model ({best_model}) outperform others?\n"
            "2. What are the strengths and weaknesses of the top 3 models?\n"
            "3. Which metrics matter most for this type of problem?\n"
            "4. Are there any concerning patterns or issues?\n"
            "5. Would ensembling improve results?\n\n"
            "Be technical but understandable. Use the metrics provided."
        )
        
        prompt = _truncate_text(prompt, MAX_CONTEXT_CHARS)
        generated = _generate_once(prompt, request_id)
        
        return _result(
            True,
            generated["answer"],
            "ok",
            request_id=request_id,
            comparison_type="model_leaderboard"
        )
    except Exception as exc:
        classified = _classify_error(exc)
        logger.exception("Model comparison explanation failed. request_id=%s status=%s", request_id, classified.status)
        return _result(False, classified.user_message, classified.status, request_id=request_id)


def suggest_accuracy_improvements(dataset_context: Dict[str, Any], current_accuracy: float) -> Dict[str, Any]:
    """Suggest specific steps to improve model accuracy"""
    request_id = uuid.uuid4().hex[:10]
    logger.info("Accuracy improvement suggestions started. request_id=%s current_accuracy=%s", request_id, current_accuracy)
    
    try:
        _configure_gemini()
        
        statistics = dataset_context.get("statistics", {})
        preprocessing = dataset_context.get("preprocessing", {})
        model_results = dataset_context.get("model_results", {})
        
        prompt = (
            "Provide specific, actionable steps to improve machine learning model accuracy.\n\n"
            f"Current Accuracy: {current_accuracy * 100:.2f}%\n"
            f"Best Model: {model_results.get('best_model')}\n\n"
            "Consider:\n"
            "1. **Data Quality Issues**: Missing values, outliers, imbalanced classes\n"
            "2. **Feature Engineering**: New features to create, features to remove\n"
            "3. **Preprocessing**: Different scaling, encoding, or normalization techniques\n"
            "4. **Model Tuning**: Hyperparameter adjustments for the best model\n"
            "5. **Ensemble Methods**: Combining multiple models\n"
            "6. **Data Collection**: More data or different data sources\n\n"
            f"Data Quality: {statistics.get('available')}\n"
            f"Preprocessing Applied: {len(preprocessing.get('encoding_summary', []))} feature encodings\n\n"
            "Rank suggestions by impact and feasibility. Be specific with techniques."
        )
        
        prompt = _truncate_text(prompt, MAX_CONTEXT_CHARS)
        generated = _generate_once(prompt, request_id)
        
        return _result(
            True,
            generated["answer"],
            "ok",
            request_id=request_id,
            improvement_type="accuracy"
        )
    except Exception as exc:
        classified = _classify_error(exc)
        logger.exception("Accuracy improvement suggestions failed. request_id=%s status=%s", request_id, classified.status)
        return _result(False, classified.user_message, classified.status, request_id=request_id)


# ============================================================
# CONVERSATION MEMORY & SESSION MANAGEMENT
# ============================================================

def save_conversation_message(session_id: str, role: str, message: str, dataset_id: Optional[int] = None, metadata: Optional[Dict] = None) -> None:
    """Save message to conversation history"""
    try:
        from ..models import ConversationHistory
        ConversationHistory.objects.create(
            session_id=session_id,
            role=role,
            message=message,
            dataset_id=dataset_id,
            metadata=metadata or {}
        )
        logger.debug("Conversation message saved. session_id=%s role=%s", session_id, role)
    except Exception as exc:
        logger.warning("Failed to save conversation message: %s", exc)


def get_conversation_history(session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve recent conversation history"""
    try:
        from ..models import ConversationHistory
        messages = ConversationHistory.objects.filter(session_id=session_id).order_by("-created_at")[:limit]
        return [
            {
                "role": msg.role,
                "message": msg.message,
                "created_at": msg.created_at.isoformat(),
                "metadata": msg.metadata
            }
            for msg in reversed(messages)
        ]
    except Exception as exc:
        logger.warning("Failed to retrieve conversation history: %s", exc)
        return []


def clear_conversation_history(session_id: str) -> bool:
    """Clear conversation history for a session"""
    try:
        from ..models import ConversationHistory
        ConversationHistory.objects.filter(session_id=session_id).delete()
        logger.info("Conversation history cleared. session_id=%s", session_id)
        return True
    except Exception as exc:
        logger.warning("Failed to clear conversation history: %s", exc)
        return False


def build_prompt_with_memory(question: str, dataset_context: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> str:
    """Build prompt with conversation history context"""
    question = (question or "").strip()
    dataset_info = dataset_context.get("dataset_information", {})
    
    # Build conversation context
    conversation_context = ""
    if conversation_history:
        conversation_context = "Previous conversation:\n"
        for msg in conversation_history[-5:]:  # Last 5 messages
            role = msg["role"].upper()
            conversation_context += f"{role}: {msg['message'][:200]}...\n"
        conversation_context += "\n"
    
    # Build main prompt
    prompt = (
        "You are an expert Data Scientist analyzing a machine learning project.\n\n"
        f"{conversation_context}"
        "Dataset Information:\n"
        f"- Name: {dataset_info.get('dataset_name')}\n"
        f"- Size: {dataset_info.get('rows')} rows × {dataset_info.get('columns')} columns\n"
        f"- Target: {dataset_info.get('target_column')}\n\n"
        "Full Dataset Context:\n"
        f"{_json(dataset_context)}\n\n"
        "User Question:\n"
        f"{question}\n\n"
        "Answer based on the dataset context and previous conversation if relevant."
    )
    
    prompt = _truncate_text(prompt, MAX_CONTEXT_CHARS)
    logger.info("Prompt with memory built. question_length=%s history_items=%s", len(question), len(conversation_history))
    return prompt
