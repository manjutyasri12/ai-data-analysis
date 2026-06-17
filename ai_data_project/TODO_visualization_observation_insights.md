# TODO: Visualization Observation & Insights (UI + Gemini)

- [x] Create `dataapp/visualization/chart_insights.py` to compute observations/insights/recommendations from `df` and chart metadata.
- [ ] Update `dataapp/visualization/charts.py` to append computed fields onto each chart dict (without changing existing chart HTML generation calls).
- [ ] Update `templates/dataapp/visualize.html` to render the new “Observation & Insights” section below every chart, including the “Explain with Gemini” button.

- [ ] Add JS for the Gemini explain button (AJAX POST) and render the Gemini response in the UI.
- [ ] Add backend endpoint in `dataapp/views.py` to accept chart payload and return Gemini explanation using existing `ask_gemini` (or prompt build) logic.
- [ ] Update URLs in `dataapp/urls.py` to route the endpoint.
- [ ] Verify with sample datasets that every chart shows Observations/Insights/Recommendation and Gemini explanation works/fails gracefully.

