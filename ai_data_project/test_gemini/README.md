# Gemini Integration Test Suite

This directory contains comprehensive tests for the Gemini AI integration in the AI Data Analysis Platform.

## Test Files

### 1. `test_gemini_connection.py`
Tests for API connectivity and configuration

### 2. `test_dataset_context.py`
Tests for dataset context building and extraction

### 3. `test_prompt_generation.py`
Tests for prompt building and template rendering

### 4. `test_report_generation.py`
Tests for executive summary, insights, and research paper generation

### 5. `test_conversation_memory.py`
Tests for conversation history storage and retrieval

### 6. `test_error_handling.py`
Tests for error classification and handling

### 7. `test_performance.py`
Tests for caching, compression, and optimization

### 8. `run_all_tests.py`
Master test runner that executes all tests

## Running Tests

```bash
cd ai_data_project
python manage.py shell < test_gemini/run_all_tests.py
```

Or run individual test files:

```bash
python manage.py shell < test_gemini/test_gemini_connection.py
python manage.py shell < test_gemini/test_dataset_context.py
python manage.py shell < test_gemini/test_prompt_generation.py
```

## Test Coverage

- ✅ API Key validation
- ✅ Gemini API connectivity
- ✅ Dataset context generation
- ✅ Prompt generation and compression
- ✅ Report generation functions
- ✅ Conversation memory management
- ✅ Error handling and classification
- ✅ Response extraction and parsing
- ✅ Caching mechanisms
- ✅ Model comparison explanations
- ✅ Data analysis recommendations
- ✅ Business insights generation

## Success Criteria

All tests should pass with:
- API connectivity verified
- No configuration errors
- Valid prompts generated
- Reports generated successfully
- Conversation history preserved
- Error handling working correctly
- Performance within acceptable ranges

## Troubleshooting

If tests fail:

1. **Missing API Key**: Add `GEMINI_API_KEY` to `.env` file
2. **API Quota**: Check your Google AI Studio quota
3. **Network Issues**: Verify internet connectivity
4. **Database Issues**: Run migrations with `python manage.py migrate`

## Continuous Integration

These tests can be integrated into CI/CD pipelines for automated verification.
