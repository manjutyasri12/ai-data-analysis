- [ ] Analyze why Gemini test runner cannot import `ai_data_project` (Django settings import path).
- [ ] Fix `ai_data_project/test_gemini/run_all_tests.py` to ensure project root is on `sys.path` before `django.setup()`.
- [ ] Add missing `asgi.py` if required by project (optional for tests).
- [ ] Re-run `python ai_data_project/test_gemini/run_all_tests.py`.
- [ ] Once Django initializes, test Gemini connectivity and API key loading.
- [ ] Ensure dataset-aware prompt generation test passes.

