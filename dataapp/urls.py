"""
URL configuration for Data Analysis App
Maps URLs to their corresponding views
"""

from django.urls import path
from . import views

app_name = 'dataapp'

urlpatterns = [
    # Home page - file upload form
    path('', views.home, name='home'),

    # Handle file upload
    path('upload/', views.upload_file, name='upload'),

    # Data analysis page - statistics
    path('analyze/', views.analyze_data, name='analyze'),

    # Visualization page - charts
    path('visualize/', views.visualize_data, name='visualize'),

    # Machine Learning prediction page (legacy)
    path('predict/', views.predict, name='predict'),

    # AI flows (dataset understanding, training, insights, reports, prediction)
    path('ai/understand/', views.ai_understand, name='ai_understand'),
    path('ai/train/', views.ai_train, name='ai_train'),
    path('ai/insights/', views.ai_insights, name='ai_insights'),
    path('ai/report/', views.ai_report, name='ai_report'),
    path('ai/predict_uploaded/', views.ai_predict_uploaded, name='ai_predict_uploaded'),
    path('models/<int:model_id>/download/<str:file_format>/', views.download_model, name='download_model'),

    # ML section - comprehensive model training
    path('ml/', views.ml_section, name='ml_section'),
    path('ml/train/', views.ml_train_model, name='ml_train_model'),

    # Clear data and return to home
    path('clear/', views.clear_data, name='clear'),
]

