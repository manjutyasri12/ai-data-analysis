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
    path('ai/report-enhanced/', views.ai_report_enhanced, name='ai_report_enhanced'),
    path('ai/predict_uploaded/', views.ai_predict_uploaded, name='ai_predict_uploaded'),
    path('ai-assistant/', views.ai_assistant, name='ai_assistant'),
    path('ai-chat/', views.ai_chat, name='ai_chat'),
    path('ai-chat-memory/', views.ai_chat_with_memory, name='ai_chat_memory'),
    
    # AI Report & Insights Generation Endpoints
    path('ai/generate/executive-summary/', views.ai_generate_executive_summary, name='ai_exec_summary'),
    path('ai/generate/business-insights/', views.ai_generate_business_insights, name='ai_business_insights'),
    path('ai/generate/research-paper/', views.ai_generate_research_paper, name='ai_research_paper'),
    path('ai/analyze/full-dataset/', views.ai_analyze_full_dataset, name='ai_analyze_full'),
    path('ai/explain/model-comparison/', views.ai_explain_model_comparison, name='ai_explain_models'),
    path('ai/suggest/accuracy-improvements/', views.ai_suggest_accuracy_improvements, name='ai_suggest_accuracy'),
    path('ai/explain/chart/', views.ai_explain_chart, name='ai_explain_chart'),

    
    # Conversation Management
    path('ai/conversation/history/', views.ai_get_conversation_history, name='ai_conv_history'),
    path('ai/conversation/clear/', views.ai_clear_conversation, name='ai_conv_clear'),
    
    # Gemini diagnostics
    path('test-gemini/', views.test_gemini, name='test_gemini'),
    
    # Model download
    path('models/<int:model_id>/download/<str:file_format>/', views.download_model, name='download_model'),

    # ML section - comprehensive model training
    path('ml/', views.ml_section, name='ml_section'),
    path('ml/train/', views.ml_train_model, name='ml_train_model'),

    # Clear data and return to home
    path('clear/', views.clear_data, name='clear'),
]

