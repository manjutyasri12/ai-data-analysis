from django.contrib import admin
from .models import PredictionHistory, TrainedModel, TrainingHistory, UploadedDataset, UploadedFile

admin.site.register(UploadedFile)
admin.site.register(UploadedDataset)
admin.site.register(TrainedModel)
admin.site.register(TrainingHistory)
admin.site.register(PredictionHistory)
