# Gemini AI Integration - Complete Documentation

## Overview

The AI Data Analysis Platform now features a **fully functional, dataset-aware Gemini AI Assistant** that intelligently understands and analyzes your uploaded datasets, trained models, and predictions.

## Key Features

### 1. **Dataset-Aware AI Assistant**
- Automatically receives complete dataset context
- Understands data quality, statistics, and relationships
- Provides intelligent recommendations based on actual data

### 2. **Comprehensive AI Capabilities**

#### Data Analysis
- Explain dataset structure and quality
- Identify missing values and data issues
- Provide data quality recommendations
- Suggest preprocessing and feature engineering steps

#### Model Analysis
- Compare trained models side-by-side
- Explain why specific models perform better
- Suggest accuracy improvements
- Provide model-specific recommendations

#### Report Generation
- **Executive Summary**: Professional project overview
- **Business Insights**: Actionable recommendations and patterns
- **Research Paper**: Academic-format analysis with methodology

#### Conversation Memory
- Maintains conversation history across sessions
- Context-aware follow-up questions
- Retrieves previous analysis and results

### 3. **Advanced Prompt Engineering**
Smart prompt templates include:
- Complete dataset information
- Statistical summaries
- Correlation matrices
- Model comparison results
- Prediction history
- Visualization metadata

---

## Installation & Setup

### 1. Install Required Package

```bash
pip install google-generativeai>=0.8.0
```

### 2. Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikeys)
2. Create a new API key
3. Copy the key

### 3. Configure Environment

Create or edit `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
```

### 4. Apply Database Migrations

```bash
python manage.py migrate
```

This creates the `ConversationHistory` table for storing chat messages.

### 5. Verify Setup

```bash
python manage.py shell
from dataapp.services.ai_assistant import validate_gemini_setup
result = validate_gemini_setup()
print(result)
```

Should show:
```python
{
    'package_installed': True,
    'dotenv_loaded': True,
    'api_key_loaded': True,
    'configured': True,
    'status': 'ok'
}
```

---

## Usage Guide

### Access the AI Assistant

1. Upload a CSV dataset from the home page
2. Navigate to **Gemini AI Assistant** in the sidebar
3. Start asking questions!

### Quick Actions

The interface provides quick access to:

#### 📊 Report Generation
- **Executive Summary**: Professional overview of your project
- **Business Insights**: Key findings and recommendations
- **Research Paper**: Academic-style analysis document

#### 🔍 Data Analysis
- **Full Dataset Analysis**: Comprehensive AI-powered assessment
- **Model Leaderboard**: Detailed comparison of trained models
- **Accuracy Improvements**: Specific steps to boost performance

#### 💡 Quick Questions
Pre-built questions for instant answers:
- "What insights can you find in this dataset?"
- "What data quality issues exist?"
- "Which features are most important?"
- "What is the best ML model for this data?"

### Chat Features

#### Smart Conversation
1. Type any question about your data
2. Gemini analyzes your complete dataset context
3. Get intelligent, data-specific answers
4. Ask follow-up questions (conversation memory remembers context)

#### Conversation History
- Click **📜 History** to view recent messages
- Previous context is automatically considered
- Clear history with **🗑️ Clear** button

---

## API Endpoints

### Chat with Conversation Memory
```
POST /ai-chat-memory/
Body: {"question": "Your question here"}
Response: {"success": true, "answer": "...", "conversation_history": [...]}
```

### Generate Reports
```
POST /ai/generate/executive-summary/
POST /ai/generate/business-insights/
POST /ai/generate/research-paper/
```

### Analysis Functions
```
POST /ai/analyze/full-dataset/
POST /ai/explain/model-comparison/
POST /ai/suggest/accuracy-improvements/
```

### Conversation Management
```
GET /ai/conversation/history/?limit=20
POST /ai/conversation/clear/
```

---

## Context Engine Details

Every Gemini request automatically includes:

### Dataset Information
- Dataset name and dimensions (rows × columns)
- Column names and data types
- Missing values per column
- Duplicate rows
- Numeric and categorical columns

### Statistical Analysis
- Mean, median, mode
- Standard deviation and variance
- Min, max, quartiles
- Skewness and kurtosis
- Distribution summaries

### Correlation Results
- Top correlated feature pairs
- Target correlations
- Correlation strength classification

### Preprocessing Summary
- Applied cleaning operations
- Encoding transformations
- Outlier handling methods
- Feature scaling information

### Model Results
- Trained model names and types
- Accuracy, precision, recall, F1-score
- R² for regression models
- MAE, MSE, RMSE values
- Training time
- Best model identification

### Prediction History
- Recent predictions made
- Input feature values
- Prediction outputs
- Prediction timestamps

---

## Advanced Features

### Model Comparison Explanation

When you ask "Why did Random Forest outperform Linear Regression?", Gemini:
1. Analyzes the complete model leaderboard
2. Compares metrics (accuracy, precision, recall, F1, etc.)
3. Considers the data characteristics
4. Provides specific reasons for performance differences
5. Suggests models that might work even better

### Dataset Analysis

The "Full Dataset Analysis" feature provides:
- **Dataset Type**: Classification, Regression, or Clustering
- **Data Quality Score**: 0-100 rating
- **Recommended ML Task**: Best problem formulation
- **Feature Importance**: Top 5 most relevant features
- **Target Suggestions**: If target not specified
- **Recommended Models**: 3-5 suited algorithms
- **Potential Issues**: Imbalance, outliers, etc.
- **Recommended Cleaning Steps**: Specific actions
- **Feature Engineering Ideas**: New features to create

---

## Error Handling

The system handles these scenarios:

### Missing API Key
```
Status: "missing_api_key"
Message: "Add GEMINI_API_KEY to your .env file"
```

### Invalid API Key
```
Status: "invalid_api_key"
Message: "Check GEMINI_API_KEY in your .env file"
```

### Quota Exceeded
```
Status: "quota_exceeded"
Message: "Check your Google AI billing/quota"
```

### Timeout
```
Status: "timeout"
Message: "Try a shorter question"
```

### No Dataset
```
Status: "dataset_not_loaded"
Message: "Please upload a CSV dataset first"
```

---

## Testing

### Run Full Test Suite

```bash
cd ai_data_project
python test_gemini/run_all_tests.py
```

### Individual Tests

```bash
# Test Gemini connection
python manage.py shell < test_gemini/test_gemini_connection.py

# Test dataset context
python manage.py shell < test_gemini/test_dataset_context.py

# Test prompts
python manage.py shell < test_gemini/test_prompt_generation.py

# Test conversation memory
python manage.py shell < test_gemini/test_conversation_memory.py
```

### Expected Output
```
✅ API Key Validation: PASSED
✅ Gemini Connectivity: PASSED
✅ Dataset Context Generation: PASSED
✅ Statistics Extraction: PASSED
✅ Correlation Analysis: PASSED
✅ Conversation Memory: PASSED
...
Total: 15/15 tests passed
🎉 ALL TESTS PASSED!
```

---

## Performance Optimization

### Context Compression
- Large datasets summarize to key statistics
- Top correlations only (not all pairs)
- Model leaderboard limited to top models
- Prediction history limited to recent predictions

### Caching Strategy
- Dataset contexts cached per session
- Prompts reused for similar questions
- Model results cached until retraining

### Token Management
- Maximum prompt size: 24,000 characters
- Response token limit: 2,048 tokens
- Automatic truncation of large contexts

---

## Troubleshooting

### Gemini not responding

1. **Check API Key**
   ```python
   from dataapp.services.ai_assistant import validate_gemini_setup
   print(validate_gemini_setup())
   ```

2. **Check Quota**
   - Visit [Google AI Studio](https://aistudio.google.com)
   - Check usage under "Billing"
   - Ensure you haven't exceeded free tier limits

3. **Check Network**
   - Verify internet connectivity
   - Check if google.generativeai can reach API

### Conversation history not saving

1. **Run migrations**
   ```bash
   python manage.py migrate
   ```

2. **Check database**
   ```python
   from dataapp.models import ConversationHistory
   print(ConversationHistory.objects.count())
   ```

### Reports generation fails

1. **Check context completeness**
   ```python
   from dataapp.services.ai_assistant import build_dataset_context
   # Verify dataset is loaded
   ```

2. **Check token limits**
   - Reduce dataset size or number of models
   - Use specific target column

---

## Example Questions

### Data Understanding
- "Explain this dataset in detail"
- "What are the main characteristics of this data?"
- "Identify any data quality issues"
- "What type of ML problem is this?"

### Feature Analysis
- "Which features are most important?"
- "How do features correlate with the target?"
- "Should I remove any columns?"
- "Suggest new features to engineer"

### Model Analysis
- "Compare these trained models"
- "Why did Random Forest perform best?"
- "What's the best model for this data?"
- "How can I improve accuracy?"

### Business Insights
- "What are the key insights from this data?"
- "What patterns should I act on?"
- "Generate business recommendations"
- "What's my next step?"

### Report Generation
- "Generate an executive summary"
- "Create business insights report"
- "Write academic research paper"

---

## Best Practices

1. **Always upload complete datasets** - Gemini provides better insights with more data
2. **Select target columns explicitly** - Improves model recommendations
3. **Train multiple models** - Enables meaningful model comparison
4. **Use conversation memory** - Ask follow-up questions for context
5. **Export reports** - Download and save generated reports
6. **Review recommendations** - Evaluate Gemini's suggestions before implementation

---

## API Rate Limits

- **Free Tier**: 60 requests per minute
- **Paid Tier**: Higher limits based on plan
- **Retry Logic**: Automatic retry on timeout (up to 2 attempts)

---

## Support & Resources

- [Google Gemini API Docs](https://ai.google.dev/docs)
- [Project GitHub Issues](link-to-repo)
- [Test Suite](./test_gemini/)
- [Error Documentation](#error-handling)

---

## Version Info

- **Gemini Model**: 1.5 Flash
- **Integration Date**: June 2026
- **Status**: Production Ready ✅
- **Last Updated**: June 2, 2026

---

## License & Attribution

Powered by Google Gemini API. See LICENSE file for details.

**Created**: Advanced AI Data Analysis Platform with Gemini Integration
