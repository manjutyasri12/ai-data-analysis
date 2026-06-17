# TODO - Gemini auto model selection + diagnostics

- [x] Implement dynamic model discovery & selection in `dataapp/services/ai_assistant.py`

  - [ ] Add `get_best_available_model()` (preferred order you provided)
  - [ ] Discover models via `genai.list_models()`
  - [ ] Map short names to fully-qualified `models/...` names
  - [ ] Select first available model that supports `generateContent`
  - [ ] Fallback to next model on errors (no crash)
  - [ ] Add logging for selected model + fallback model + failed model + elapsed time
- [ ] Update assistant code to use selected model everywhere (replace hardcoded GEMINI_MODEL)
- [ ] Add `/test-gemini/` health endpoint
  - [ ] Return API Status
  - [ ] Available Models
  - [ ] Selected Model
  - [ ] Gemini Response Test
- [ ] Fix chart/statmodels dependency
  - [ ] `pip install statsmodels`
  - [ ] Verify imports
  - [ ] Fix chart context generation if needed
- [ ] Testing
  - [ ] Run `ai_data_project/test_gemini/run_all_tests.py`
  - [ ] Verify dataset context works
  - [ ] Verify AI chat works
  - [ ] Verify report generation works
  - [ ] Verify model comparison explanation works

