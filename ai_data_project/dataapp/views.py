import json
import logging
import os
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .auto_train import detect_task_type, predict_dataframe, save_best_model, train_model_set
from .forms import CsvUploadForm, TargetSelectionForm
from .ml_models import all_model_names, get_models
from .models import PredictionHistory, TrainedModel, TrainingHistory, UploadedDataset, UploadedFile, ConversationHistory
from .preprocessing import (
    changed_table_html,
    clean_dataset_for_display,
    dataframe_from_session_json,
    dataframe_to_session_json,
    dataset_overview,
)
from .services.ai_assistant import (
    ask_gemini,


    build_dataset_context,
    run_diagnostics,
    generate_executive_summary,
    generate_business_insights,
    generate_research_paper,
    analyze_entire_dataset,
    explain_model_comparison,
    suggest_accuracy_improvements,
    save_conversation_message,
    get_conversation_history,
    clear_conversation_history,
    build_prompt_with_memory,
)
from .visualization.charts import smart_charts


logger = logging.getLogger(__name__)
CLEANING_VERSION = "salary-domain-v2"


def _salary_debug_stats(df: pd.DataFrame) -> Dict[str, Any]:
    if "Monthly_Salary" not in df.columns:
        return {"present": False}
    salary = pd.to_numeric(df["Monthly_Salary"], errors="coerce")
    return {
        "present": True,
        "dtype": str(df["Monthly_Salary"].dtype),
        "numeric_dtype": str(salary.dtype),
        "stats": salary.describe().to_dict(),
        "negative_count": int((salary < 0).sum()),
        "sentinel_999999_count": int((salary == 999999).sum()),
    }


def _current_df(request) -> pd.DataFrame:
    data_json = request.session.get("data")
    if not data_json:
        raise ValueError("Please upload a CSV dataset first.")
    df = dataframe_from_session_json(data_json)
    logger.info(
        "Loaded raw dataframe from session key=data shape=%s salary=%s",
        df.shape,
        _salary_debug_stats(df),
    )
    return df


def _current_clean_df(request) -> pd.DataFrame:
    if request.session.get("cleaning_version") != CLEANING_VERSION and request.session.get("data"):
        raw_df = dataframe_from_session_json(request.session["data"])
        cleaned_df, preprocessing_report = clean_dataset_for_display(raw_df)
        request.session["cleaned_data"] = dataframe_to_session_json(cleaned_df)
        request.session["preprocessing_report"] = preprocessing_report
        request.session["cleaning_version"] = CLEANING_VERSION
        request.session.modified = True
        logger.info(
            "Rebuilt stale cleaned dataframe from raw session data: raw_shape=%s cleaned_shape=%s salary=%s",
            raw_df.shape,
            cleaned_df.shape,
            _salary_debug_stats(cleaned_df),
        )

    session_key = "cleaned_data" if request.session.get("cleaned_data") else "data"
    data_json = request.session.get(session_key)
    if not data_json:
        raise ValueError("Please upload a CSV dataset first.")
    df = dataframe_from_session_json(data_json)
    logger.info(
        "Loaded dataframe from session key=%s shape=%s salary=%s",
        session_key,
        df.shape,
        _salary_debug_stats(df),
    )
    return df


def _target_form(request, df: pd.DataFrame, post: bool = False) -> TargetSelectionForm:
    data = request.POST if post else None
    form = TargetSelectionForm(data=data, columns=df.columns.tolist())
    selected = request.session.get("last_target_column")
    if not post and selected in df.columns:
        form.initial["target_column"] = selected
    return form


def _metric_percent(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%"


def _safe_record(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def home(request):
    return render(request, "dataapp/home.html", {"form": CsvUploadForm()})


def upload_file(request):
    if request.method != "POST":
        return redirect("dataapp:home")

    form = CsvUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, "dataapp/home.html", {"form": form, "error": form.errors.as_text()})

    csv_file = form.cleaned_data["csv_file"]
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            raise ValueError("The uploaded CSV is empty.")
        logger.info(
            "CSV upload read: file=%s shape=%s columns=%s salary=%s",
            csv_file.name,
            df.shape,
            df.columns.tolist(),
            _salary_debug_stats(df),
        )

        overview = dataset_overview(df)
        cleaned_df, preprocessing_report = clean_dataset_for_display(df)
        logger.info(
            "CSV upload cleaned: file=%s shape=%s salary=%s domain_rules=%s outliers=%s",
            csv_file.name,
            cleaned_df.shape,
            _salary_debug_stats(cleaned_df),
            preprocessing_report.get("domain_rules", []),
            preprocessing_report.get("outliers", []),
        )

        dataset = UploadedDataset(
            original_name=csv_file.name,
            rows=int(df.shape[0]),
            columns=int(df.shape[1]),
            size_bytes=int(csv_file.size),
            column_schema=overview["dtypes"],
            missing_values=overview["missing_values"],
            preprocessing_report=preprocessing_report,
        )
        csv_file.seek(0)
        dataset.file.save(csv_file.name, csv_file, save=True)
        UploadedFile.objects.create(file_name=csv_file.name, file_path=dataset.file.name)

        request.session["data"] = dataframe_to_session_json(df)
        request.session["cleaned_data"] = dataframe_to_session_json(cleaned_df)
        request.session["file_name"] = csv_file.name
        request.session["dataset_id"] = dataset.id
        request.session["preprocessing_report"] = preprocessing_report
        request.session["cleaning_version"] = CLEANING_VERSION
        request.session.modified = True
        logger.info(
            "CSV upload stored session data: raw_shape=%s cleaned_shape=%s raw_json_bytes=%s cleaned_json_bytes=%s",
            df.shape,
            cleaned_df.shape,
            len(request.session["data"]),
            len(request.session["cleaned_data"]),
        )
        logger.info(
            "CSV upload rendering template with cleaned dataframe: preview_rows=%s changed_table_rows=%s salary=%s",
            min(20, len(cleaned_df)),
            min(120, len(cleaned_df)),
            _salary_debug_stats(cleaned_df),
        )

        return render(
            request,
            "dataapp/upload_success.html",
            {
                "file_name": csv_file.name,
                "rows": int(df.shape[0]),
                "cols": int(df.shape[1]),
                "overview": overview,
                "preprocessing_report": preprocessing_report,
                "preview": df.head(20).to_html(classes="table table-sm table-striped", index=False),
                "cleaned_preview": cleaned_df.head(20).to_html(classes="table table-sm table-striped", index=False),
                "cleaned_changed_table": changed_table_html(df, cleaned_df, max_rows=120),
            },
        )
    except Exception as exc:
        return render(
            request,
            "dataapp/home.html",
            {"form": CsvUploadForm(), "error": f"Could not read CSV: {exc}"},
        )


def analyze_data(request):
    try:
        df = _current_clean_df(request)
    except Exception:
        return redirect("dataapp:home")

    numeric = df.select_dtypes(include=[np.number])
    stats_rows: Dict[str, Dict[str, Any]] = {}
    for col in numeric.columns:
        series = numeric[col].dropna()
        mode = series.mode()
        stats_rows[col] = {
            "mean": round(float(series.mean()), 6) if not series.empty else None,
            "median": round(float(series.median()), 6) if not series.empty else None,
            "mode": round(float(mode.iloc[0]), 6) if not mode.empty else None,
            "variance": round(float(series.var()), 6) if len(series) > 1 else None,
            "std": round(float(series.std()), 6) if len(series) > 1 else None,
            "min": round(float(series.min()), 6) if not series.empty else None,
            "q1": round(float(series.quantile(0.25)), 6) if not series.empty else None,
            "q3": round(float(series.quantile(0.75)), 6) if not series.empty else None,
            "max": round(float(series.max()), 6) if not series.empty else None,
            "skewness": round(float(series.skew()), 6) if len(series) > 2 else None,
            "kurtosis": round(float(series.kurtosis()), 6) if len(series) > 3 else None,
        }
    corr_html = (
        numeric.corr(numeric_only=True).round(4).to_html(classes="table table-sm table-bordered")
        if len(numeric.columns) >= 2
        else ""
    )
    return render(
        request,
        "dataapp/statistics.html",
        {
            "file_name": request.session.get("file_name", "data.csv"),
            "stats_rows": stats_rows,
            "describe_table": numeric.describe().T.round(4).to_html(classes="table table-sm table-striped") if not numeric.empty else "",
            "correlation_table": corr_html,
        },
    )


def visualize_data(request):
    try:
        df = _current_clean_df(request)
    except Exception:
        return redirect("dataapp:home")
    target = request.GET.get("target") or request.session.get("last_target_column")
    try:
        charts = smart_charts(df, target if target in df.columns else None)
    except Exception as exc:
        charts = []
        messages.error(request, f"Chart generation failed safely: {exc}")
    return render(
        request,
        "dataapp/visualize.html",
        {
            "file_name": request.session.get("file_name", "data.csv"),
            "charts": charts,
            "columns": df.columns.tolist(),
            "selected_target": target or "",
        },
    )


def _understanding_payload(df: pd.DataFrame, target_column: str, train_result=None) -> Dict[str, Any]:
    problem_type = detect_task_type(df, target_column)
    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical = [c for c in df.columns if c not in numeric]
    quality_score = max(0, 100 - int(df.isna().sum().sum() / max(1, df.size) * 100) - min(30, int(df.duplicated().sum())))
    imbalance = None
    if problem_type == "classification":
        counts = df[target_column].value_counts(dropna=False)
        if not counts.empty:
            imbalance = {
                "largest_class": str(counts.index[0]),
                "largest_percent": round(float(counts.iloc[0] / counts.sum() * 100), 2),
                "class_count": int(len(counts)),
            }
    correlations = []
    if target_column in numeric:
        corr = df[numeric].corr(numeric_only=True)[target_column].drop(labels=[target_column], errors="ignore")
        correlations = [
            {"feature": k, "correlation": round(float(v), 4)}
            for k, v in corr.abs().sort_values(ascending=False).head(8).items()
            if not pd.isna(v)
        ]
    recommended = train_result.best_model_name if train_result else ("Random Forest Classifier" if problem_type == "classification" else "Random Forest Regressor")
    return {
        "dataset_type": "Classification" if problem_type == "classification" else "Regression",
        "best_ml_approach": "Supervised learning with preprocessing, cross-validation, and model comparison.",
        "important_features": [c["feature"] for c in correlations[:5]] or numeric[:5] or categorical[:5],
        "recommended_model": recommended,
        "why_model_selected": "The platform selects the highest valid accuracy score after filtering failed or None-valued model results.",
        "quality_score": quality_score,
        "imbalance": imbalance,
        "correlations": correlations,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
    }


def ai_understand(request):
    try:
        df = _current_clean_df(request)
    except Exception:
        return redirect("dataapp:home")
    form = _target_form(request, df, post=request.method == "POST")
    payload = None
    if request.method == "POST" and form.is_valid():
        target = form.cleaned_data["target_column"]
        request.session["last_target_column"] = target
        request.session.modified = True
        payload = _understanding_payload(df, target)
    return render(request, "dataapp/ai_understand.html", {"form": form, "understanding": payload})


def _persist_training_result(request, result, saved_paths):
    dataset = None
    dataset_id = request.session.get("dataset_id")
    if dataset_id:
        dataset = UploadedDataset.objects.filter(id=dataset_id).first()
    best = next((r for r in result.leaderboard if r.get("model_name") == result.best_model_name), {})
    trained_model = TrainedModel.objects.create(
        dataset=dataset,
        model_name=result.best_model_name or "",
        problem_type=result.problem_type,
        target_column=result.metadata["target_column"],
        accuracy=best.get("accuracy"),
        precision=best.get("precision"),
        recall=best.get("recall"),
        f1_score=best.get("f1_score"),
        r2_score=best.get("r2_score"),
        mae=best.get("mae"),
        rmse=best.get("rmse"),
        cv_score=best.get("cv_score"),
        training_time=best.get("training_time"),
        feature_names=result.feature_columns,
        metadata=result.metadata,
    )
    trained_model.joblib_file.name = os.path.relpath(saved_paths["joblib_path"], settings.MEDIA_ROOT).replace("\\", "/")
    trained_model.pickle_file.name = os.path.relpath(saved_paths["pickle_path"], settings.MEDIA_ROOT).replace("\\", "/")
    trained_model.save()
    TrainingHistory.objects.create(
        dataset=dataset,
        target_column=result.metadata["target_column"],
        problem_type=result.problem_type,
        best_model_name=result.best_model_name or "",
        best_accuracy=result.best_accuracy,
        leaderboard=result.leaderboard,
        failed_models=result.failed_models,
    )
    request.session["last_model_id"] = trained_model.id
    request.session["last_train_result"] = result.leaderboard
    request.session.modified = True
    return trained_model


def ai_train(request):
    try:
        df = _current_clean_df(request)
    except Exception:
        return redirect("dataapp:home")

    form = _target_form(request, df, post=request.method == "POST")
    context = {"form": form, "file_name": request.session.get("file_name", "data.csv")}
    if request.method == "POST" and form.is_valid():
        target = form.cleaned_data["target_column"]
        request.session["last_target_column"] = target
        try:
            result = train_model_set(df, target)
            saved = save_best_model(result, request.session.get("file_name", "dataset.csv"))
            trained_model = _persist_training_result(request, result, saved)
            context.update(
                {
                    "success": True,
                    "result": result,
                    "leaderboard": result.leaderboard,
                    "trained_model": trained_model,
                    "best_accuracy_display": _metric_percent(result.best_accuracy),
                }
            )
        except Exception as exc:
            context["error"] = str(exc)
    return render(request, "dataapp/ai_train.html", context)


def ml_section(request):
    return ai_train(request)


def ml_train_model(request):
    try:
        df = _current_clean_df(request)
    except Exception:
        return redirect("dataapp:home")
    target = request.POST.get("target_column") or request.session.get("last_target_column")
    problem_type = detect_task_type(df, target) if target in df.columns else "classification"
    context = {
        "columns": df.columns.tolist(),
        "models": all_model_names(),
        "selected_target": target or "",
        "problem_type": problem_type,
        "result": None,
    }
    if request.method == "POST" and target in df.columns and request.POST.get("model_name"):
        try:
            selected_model = request.POST["model_name"]
            model_pool = get_models(problem_type)
            if selected_model not in model_pool:
                raise ValueError("Selected model is not available for the detected task type.")
            all_results = train_model_set(df, target)
            row = next((r for r in all_results.leaderboard if r["model_name"] == selected_model), None)
            context["result"] = row
        except Exception as exc:
            context["error"] = str(exc)
    return render(request, "dataapp/ml_train_model.html", context)


def ai_insights(request):
    return ai_understand(request)


def ai_report(request):
    try:
        df = _current_clean_df(request)
    except Exception:
        return redirect("dataapp:home")
    form = _target_form(request, df, post=request.method == "POST")
    context = {"form": form}
    if request.method == "POST" and form.is_valid():
        target = form.cleaned_data["target_column"]
        try:
            result = train_model_set(df, target)
            context.update({"understanding": _understanding_payload(df, target, result), "leaderboard": result.leaderboard})
        except Exception as exc:
            context["error"] = str(exc)
    return render(request, "dataapp/ai_report.html", context)


def _saved_models() -> List[TrainedModel]:
    return list(TrainedModel.objects.exclude(joblib_file="").order_by("-created_at")[:50])


def predict(request):
    try:
        df = _current_clean_df(request)
    except Exception:
        df = pd.DataFrame()
    models = _saved_models()
    selected_model = TrainedModel.objects.filter(id=request.POST.get("model_id")).first() if request.method == "POST" else None
    if not selected_model and request.session.get("last_model_id"):
        selected_model = TrainedModel.objects.filter(id=request.session["last_model_id"]).first()
    context = {"models": models, "selected_model": selected_model, "columns": df.columns.tolist()}
    if request.method == "POST" and selected_model:
        try:
            payload = joblib.load(selected_model.joblib_file.path)
            feature_columns = selected_model.feature_names
            if request.FILES.get("test_csv"):
                test_df = pd.read_csv(request.FILES["test_csv"])
                predictions = predict_dataframe(payload, test_df)
                rows = [{"row": i + 1, "prediction": _safe_record(v)} for i, v in enumerate(predictions[:200])]
                context["predictions"] = rows
                PredictionHistory.objects.create(
                    trained_model=selected_model,
                    input_data={"uploaded_rows": int(len(test_df))},
                    prediction={"sample": rows[:20]},
                )
            else:
                row = {col: request.POST.get(f"feature_{col}") for col in feature_columns}
                input_df = pd.DataFrame([row])
                prediction = predict_dataframe(payload, input_df)[0]
                context["single_prediction"] = _safe_record(prediction)
                PredictionHistory.objects.create(
                    trained_model=selected_model,
                    input_data=row,
                    prediction={"value": _safe_record(prediction)},
                )
        except Exception as exc:
            context["error"] = str(exc)
    return render(request, "dataapp/predict.html", context)


def ai_predict_uploaded(request):
    return predict(request)


def _latest_ai_context(request, df: pd.DataFrame) -> Dict[str, Any]:
    dataset = UploadedDataset.objects.filter(id=request.session.get("dataset_id")).first()
    trained_model = TrainedModel.objects.filter(id=request.session.get("last_model_id")).first()
    if not trained_model and dataset:
        trained_model = TrainedModel.objects.filter(dataset=dataset).order_by("-created_at").first()

    training_history = None
    if dataset:
        training_history = TrainingHistory.objects.filter(dataset=dataset).order_by("-created_at").first()

    model_results = request.session.get("last_train_result", [])
    best_model = trained_model.model_name if trained_model else None
    accuracy = trained_model.accuracy if trained_model else None
    if training_history:
        model_results = training_history.leaderboard or model_results
        best_model = best_model or training_history.best_model_name
        accuracy = accuracy if accuracy is not None else training_history.best_accuracy

    predictions = []
    prediction_query = PredictionHistory.objects.all().order_by("-created_at")
    if trained_model:
        prediction_query = prediction_query.filter(trained_model=trained_model)
    for item in prediction_query[:10]:
        predictions.append(
            {
                "input_data": item.input_data,
                "prediction": item.prediction,
                "created_at": item.created_at.isoformat(),
            }
        )

    target_column = request.session.get("last_target_column") or (trained_model.target_column if trained_model else None)
    charts = []
    try:
        charts = smart_charts(df, target_column if target_column in df.columns else None)
    except Exception as exc:
        logger.warning("Gemini chart context generation skipped safely: %s", exc)

    return build_dataset_context(
        df=df,
        dataset_name=request.session.get("file_name") or (dataset.original_name if dataset else "uploaded dataset"),
        target_column=target_column,
        preprocessing_report=request.session.get("preprocessing_report") or (dataset.preprocessing_report if dataset else {}),
        model_comparison_results=model_results,
        best_model=best_model,
        accuracy=accuracy,
        prediction_results=predictions,
        chart_results=charts,
    )


def ai_assistant(request):
    return render(
        request,
        "dataapp/ai_assistant.html",
        {
            "file_name": request.session.get("file_name", ""),
            "has_dataset": bool(request.session.get("data") or request.session.get("cleaned_data")),
        },
    )


@require_POST
def ai_chat(request):
    logger.info("AI chat request received. method=%s content_length=%s", request.method, len(request.body or b""))
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        logger.warning("AI chat rejected invalid JSON payload.")
        return JsonResponse(
            {"success": False, "status": "invalid_payload", "error": "Invalid JSON request."},
            status=400,
        )

    question = (payload.get("question") or "").strip()
    if not question:
        logger.warning("AI chat rejected empty question.")
        return JsonResponse(
            {"success": False, "status": "empty_question", "error": "Please type a question before asking Gemini."},
            status=400,
        )

    try:
        df = _current_clean_df(request)
    except Exception:
        logger.warning("AI chat rejected because no dataset is loaded.")
        return JsonResponse(
            {
                "success": False,
                "status": "dataset_not_loaded",
                "error": "Dataset not loaded. Please upload a CSV dataset first.",
            },
            status=400,
        )

    context = _latest_ai_context(request, df)
    logger.info(
        "AI chat context ready. dataset=%s rows=%s columns=%s target=%s",
        context.get("dataset_information", {}).get("dataset_name"),
        context.get("dataset_information", {}).get("rows"),
        context.get("dataset_information", {}).get("columns"),
        context.get("dataset_information", {}).get("target_column"),
    )
    result = ask_gemini(question, context)
    logger.info("AI chat response status=%s success=%s request_id=%s", result.get("status"), result.get("success"), result.get("request_id"))
    return JsonResponse(result, status=200 if result["success"] else 400)


@require_GET
def test_gemini(request):
    sample_context = None
    try:
        df = _current_clean_df(request)
        sample_context = _latest_ai_context(request, df)
    except Exception:
        logger.info("Gemini diagnostics running without dataset context.")
    result = run_diagnostics(sample_context)
    if result["success"] and request.GET.get("format") == "text":
        return HttpResponse("Gemini working successfully", content_type="text/plain")
    if result["success"]:
        return JsonResponse(result)
    return JsonResponse(result, status=400)


def download_model(request, model_id: int, file_format: str):
    model = get_object_or_404(TrainedModel, id=model_id)
    file_field = model.pickle_file if file_format == "pkl" else model.joblib_file
    if not file_field:
        raise Http404("Model file not found.")
    return FileResponse(open(file_field.path, "rb"), as_attachment=True, filename=os.path.basename(file_field.name))


def clear_data(request):
    for key in ["data", "cleaned_data", "file_name", "dataset_id", "preprocessing_report", "cleaning_version", "last_target_column", "last_model_id", "last_train_result"]:
        request.session.pop(key, None)
    return HttpResponseRedirect(reverse("dataapp:home"))


# ============================================================
# NEW AI REPORT & INSIGHTS ENDPOINTS
# ============================================================


@require_POST
def ai_explain_chart(request):
    """Explain a single visualization/chart using Gemini."""
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "status": "invalid_payload", "error": "Invalid JSON request."}, status=400)

    try:
        df = _current_clean_df(request)
    except Exception:
        return JsonResponse({"success": False, "status": "dataset_not_loaded", "error": "Please upload a dataset first."}, status=400)

    context = _latest_ai_context(request, df)

    chart_meta = payload if isinstance(payload, dict) else {}
    title = chart_meta.get("title") or chart_meta.get("chart_title") or "Chart"
    kind = chart_meta.get("kind") or "Unknown"
    observations = chart_meta.get("observations") or []
    key_insights = chart_meta.get("key_insights") or []
    recommendation = chart_meta.get("recommendation") or ""

    question = (
        "Explain this chart to a business user."
        "\n\nChart Title: " + str(title) +
        "\nChart Type: " + str(kind) +
        "\n\nObservations (data-driven):\n- " + "\n- ".join(observations[:5]) +
        "\n\nKey Insights (data-driven):\n- " + "\n- ".join(key_insights[:5]) +
        "\n\nRecommendation (precomputed):\n" + str(recommendation) +
        "\n\nIn your answer include: what the graph means, important findings, ML implications, and business interpretation."
    )

    result = ask_gemini(question, context)
    return JsonResponse(result, status=200 if result.get("success") else 400)



@require_POST
def ai_generate_executive_summary(request):
    """Generate executive summary of dataset analysis"""
    logger.info("Executive summary request received.")
    try:
        df = _current_clean_df(request)
    except Exception:
        return JsonResponse(
            {"success": False, "status": "dataset_not_loaded", "error": "Please upload a dataset first."},
            status=400,
        )
    
    try:
        context = _latest_ai_context(request, df)
        result = generate_executive_summary(context)
        return JsonResponse(result)
    except Exception as exc:
        logger.exception("Executive summary generation failed: %s", exc)
        return JsonResponse(
            {"success": False, "status": "error", "error": str(exc)},
            status=500,
        )


@require_POST
def ai_generate_business_insights(request):
    """Generate business insights from dataset"""
    logger.info("Business insights request received.")
    try:
        df = _current_clean_df(request)
    except Exception:
        return JsonResponse(
            {"success": False, "status": "dataset_not_loaded", "error": "Please upload a dataset first."},
            status=400,
        )
    
    try:
        context = _latest_ai_context(request, df)
        result = generate_business_insights(context)
        return JsonResponse(result)
    except Exception as exc:
        logger.exception("Business insights generation failed: %s", exc)
        return JsonResponse(
            {"success": False, "status": "error", "error": str(exc)},
            status=500,
        )


@require_POST
def ai_generate_research_paper(request):
    """Generate research paper content"""
    logger.info("Research paper request received.")
    try:
        df = _current_clean_df(request)
    except Exception:
        return JsonResponse(
            {"success": False, "status": "dataset_not_loaded", "error": "Please upload a dataset first."},
            status=400,
        )
    
    try:
        context = _latest_ai_context(request, df)
        result = generate_research_paper(context)
        return JsonResponse(result)
    except Exception as exc:
        logger.exception("Research paper generation failed: %s", exc)
        return JsonResponse(
            {"success": False, "status": "error", "error": str(exc)},
            status=500,
        )


@require_POST
def ai_analyze_full_dataset(request):
    """Perform comprehensive AI analysis of entire dataset"""
    logger.info("Full dataset analysis request received.")
    try:
        df = _current_clean_df(request)
    except Exception:
        return JsonResponse(
            {"success": False, "status": "dataset_not_loaded", "error": "Please upload a dataset first."},
            status=400,
        )
    
    try:
        target_column = request.POST.get("target_column") or request.session.get("last_target_column")
        result = analyze_entire_dataset(df, target_column if target_column in df.columns else None)
        return JsonResponse(result)
    except Exception as exc:
        logger.exception("Full dataset analysis failed: %s", exc)
        return JsonResponse(
            {"success": False, "status": "error", "error": str(exc)},
            status=500,
        )


@require_POST
def ai_explain_model_comparison(request):
    """Explain why best model performed better"""
    logger.info("Model comparison explanation request received.")
    try:
        df = _current_clean_df(request)
    except Exception:
        return JsonResponse(
            {"success": False, "status": "dataset_not_loaded", "error": "Please upload a dataset first."},
            status=400,
        )
    
    try:
        model_results = request.session.get("last_train_result", [])
        if not model_results:
            return JsonResponse(
                {"success": False, "status": "no_models", "error": "No trained models available. Please train models first."},
                status=400,
            )
        
        best_model = request.POST.get("best_model") or request.session.get("last_model_name", "Unknown")
        result = explain_model_comparison(model_results, best_model)
        return JsonResponse(result)
    except Exception as exc:
        logger.exception("Model comparison explanation failed: %s", exc)
        return JsonResponse(
            {"success": False, "status": "error", "error": str(exc)},
            status=500,
        )


@require_POST
def ai_suggest_accuracy_improvements(request):
    """Suggest ways to improve model accuracy"""
    logger.info("Accuracy improvement suggestions request received.")
    try:
        df = _current_clean_df(request)
    except Exception:
        return JsonResponse(
            {"success": False, "status": "dataset_not_loaded", "error": "Please upload a dataset first."},
            status=400,
        )
    
    try:
        context = _latest_ai_context(request, df)
        current_accuracy = float(request.POST.get("accuracy", 0.0))
        result = suggest_accuracy_improvements(context, current_accuracy)
        return JsonResponse(result)
    except Exception as exc:
        logger.exception("Accuracy improvement suggestions failed: %s", exc)
        return JsonResponse(
            {"success": False, "status": "error", "error": str(exc)},
            status=500,
        )


@require_POST
def ai_chat_with_memory(request):
    """AI chat with conversation memory support"""
    logger.info("AI chat with memory request received.")
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        logger.warning("Invalid JSON payload.")
        return JsonResponse(
            {"success": False, "status": "invalid_payload", "error": "Invalid JSON request."},
            status=400,
        )
    
    question = (payload.get("question") or "").strip()
    session_id = request.session.session_key or "default"
    
    if not question:
        return JsonResponse(
            {"success": False, "status": "empty_question", "error": "Please type a question."},
            status=400,
        )
    
    try:
        df = _current_clean_df(request)
    except Exception:
        return JsonResponse(
            {"success": False, "status": "dataset_not_loaded", "error": "Dataset not loaded. Please upload a CSV first."},
            status=400,
        )
    
    try:
        # Get conversation history
        history = get_conversation_history(session_id, limit=10)
        
        # Build context with memory
        context = _latest_ai_context(request, df)
        
        # Save user message
        dataset_id = request.session.get("dataset_id")
        save_conversation_message(session_id, "user", question, dataset_id=dataset_id)
        
        # Generate response
        result = ask_gemini(question, context)
        
        # Save assistant message if successful
        if result.get("success"):
            save_conversation_message(
                session_id,
                "assistant",
                result.get("answer", ""),
                dataset_id=dataset_id,
                metadata={"request_id": result.get("request_id"), "finish_reason": result.get("finish_reason")}
            )
        
        # Add history to response
        result["conversation_history"] = get_conversation_history(session_id, limit=5)
        return JsonResponse(result, status=200 if result["success"] else 400)
    except Exception as exc:
        logger.exception("Chat with memory failed: %s", exc)
        return JsonResponse(
            {"success": False, "status": "error", "error": str(exc)},
            status=500,
        )


@require_GET
def ai_get_conversation_history(request):
    """Retrieve conversation history for session"""
    logger.info("Conversation history request received.")
    try:
        session_id = request.session.session_key or "default"
        limit = int(request.GET.get("limit", 20))
        history = get_conversation_history(session_id, limit=min(limit, 100))
        return JsonResponse({"success": True, "history": history})
    except Exception as exc:
        logger.exception("Failed to retrieve conversation history: %s", exc)
        return JsonResponse(
            {"success": False, "error": str(exc)},
            status=500,
        )


@require_POST
def ai_clear_conversation(request):
    """Clear conversation history"""
    logger.info("Clear conversation request received.")
    try:
        session_id = request.session.session_key or "default"
        success = clear_conversation_history(session_id)
        return JsonResponse(
            {"success": success, "message": "Conversation cleared" if success else "Failed to clear conversation"}
        )
    except Exception as exc:
        logger.exception("Failed to clear conversation: %s", exc)
        return JsonResponse(
            {"success": False, "error": str(exc)},
            status=500,
        )


# Enhanced AI Report with Gemini-powered analysis
def ai_report_enhanced(request):
    """Enhanced AI report page with multiple generation options"""
    try:
        df = _current_clean_df(request)
    except Exception:
        return redirect("dataapp:home")
    
    form = _target_form(request, df, post=request.method == "POST")
    context = {"form": form, "file_name": request.session.get("file_name", "data.csv")}
    
    if request.method == "POST" and form.is_valid():
        target = form.cleaned_data["target_column"]
        request.session["last_target_column"] = target
        try:
            result = train_model_set(df, target)
            ai_context = _latest_ai_context(request, df)
            context.update({
                "understanding": _understanding_payload(df, target, result),
                "leaderboard": result.leaderboard,
                "has_models": True,
                "best_accuracy": result.best_accuracy,
            })
        except Exception as exc:
            context["error"] = str(exc)
    
    return render(request, "dataapp/ai_report_enhanced.html", context)
