from django.db import models


class UploadedDataset(models.Model):
    original_name = models.CharField(max_length=255)
    file = models.FileField(upload_to="datasets/")
    rows = models.PositiveIntegerField(default=0)
    columns = models.PositiveIntegerField(default=0)
    size_bytes = models.PositiveIntegerField(default=0)
    column_schema = models.JSONField(default=dict, blank=True)
    missing_values = models.JSONField(default=dict, blank=True)
    preprocessing_report = models.JSONField(default=dict, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.original_name


class UploadedFile(models.Model):
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=500)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.file_name} - {self.uploaded_at:%Y-%m-%d %H:%M}"


class TrainedModel(models.Model):
    dataset = models.ForeignKey(
        UploadedDataset,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="trained_models",
    )
    model_name = models.CharField(max_length=120)
    problem_type = models.CharField(max_length=40)
    target_column = models.CharField(max_length=255)
    accuracy = models.FloatField(null=True, blank=True)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    r2_score = models.FloatField(null=True, blank=True)
    mae = models.FloatField(null=True, blank=True)
    rmse = models.FloatField(null=True, blank=True)
    cv_score = models.FloatField(null=True, blank=True)
    training_time = models.FloatField(null=True, blank=True)
    joblib_file = models.FileField(upload_to="models/", null=True, blank=True)
    pickle_file = models.FileField(upload_to="models/", null=True, blank=True)
    feature_names = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.model_name} on {self.target_column}"


class TrainingHistory(models.Model):
    dataset = models.ForeignKey(
        UploadedDataset,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="training_history",
    )
    target_column = models.CharField(max_length=255)
    problem_type = models.CharField(max_length=40)
    best_model_name = models.CharField(max_length=120, blank=True)
    best_accuracy = models.FloatField(null=True, blank=True)
    leaderboard = models.JSONField(default=list, blank=True)
    failed_models = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.problem_type} training for {self.target_column}"


class PredictionHistory(models.Model):
    trained_model = models.ForeignKey(
        TrainedModel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="predictions",
    )
    input_data = models.JSONField(default=dict, blank=True)
    prediction = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Prediction {self.pk}"
