import os
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .auto_train import detect_task_type, predict_dataframe, save_best_model, train_model_set
from .forms import CsvUploadForm, TargetSelectionForm
from .ml_models import all_model_names, get_models
from .models import PredictionHistory, TrainedModel, TrainingHistory, UploadedDataset, UploadedFile
from .preprocessing import (
    changed_table_html,
    clean_dataset_for_display,
    dataframe_from_session_json,
    dataframe_to_session_json,
    dataset_overview,
)
from .visualization.charts import smart_charts


def _current_df(request) -> pd.DataFrame:
    data_json = request.session.get("data")
    if not data_json:
        raise ValueError("Please upload a CSV dataset first.")
    return dataframe_from_session_json(data_json)


def _current_clean_df(request) -> pd.DataFrame:
    data_json = request.session.get("cleaned_data") or request.session.get("data")
    if not data_json:
        raise ValueError("Please upload a CSV dataset first.")
    return dataframe_from_session_json(data_json)


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

        overview = dataset_overview(df)
        cleaned_df, preprocessing_report = clean_dataset_for_display(df)

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
        request.session.modified = True

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


def download_model(request, model_id: int, file_format: str):
    model = get_object_or_404(TrainedModel, id=model_id)
    file_field = model.pickle_file if file_format == "pkl" else model.joblib_file
    if not file_field:
        raise Http404("Model file not found.")
    return FileResponse(open(file_field.path, "rb"), as_attachment=True, filename=os.path.basename(file_field.name))


def clear_data(request):
    for key in ["data", "cleaned_data", "file_name", "dataset_id", "last_target_column", "last_model_id", "last_train_result"]:
        request.session.pop(key, None)
    return HttpResponseRedirect(reverse("dataapp:home"))
