# TODO - AI Data Analysis Django ML Fixes

## Step 1: Fix AUTO TRAIN crash + best-model selection
- [ ] Update `dataapp/ai_pipeline.py` to never sort/compare `None` scores
- [ ] Skip failed models entirely from leaderboard sorting
- [ ] Select best by highest metric only among successful models
- [ ] Re-train the best estimator consistently and save it

## Step 2: Implement full ML metrics + results table data
- [ ] Compute Accuracy/Precision/Recall/F1 for classification
- [ ] Compute R2/MAE/RMSE for regression
- [ ] Track Training Time and (best-effort) CV score
- [ ] Update `views.py` + templates to render results table in descending order

## Step 3: Upgrade dataset type auto-detection
- [ ] Implement your explicit rules for target datatype -> regression/classification

## Step 4: Ensure preprocessing pipeline correctness
- [ ] Verify missing values, encoding, scaling, and train/test split are applied properly

## Step 5: Save best model + metadata to database
- [ ] Add DB model for training metadata in `dataapp/models.py`
- [ ] Save metadata when saving the best model

## Step 6: Frontend UX: ML section + result cards + downloads
- [ ] Update `templates/dataapp/ai_train.html` with dropdown + buttons + loader
- [ ] Create `templates/dataapp/ml_results.html` for professional results UI
- [ ] Add trained model status card + explanation card
- [ ] Add download buttons for joblib/pickle + view report button (best-effort)

## Step 7: Chart
- [ ] Create model comparison bar chart highlighting best model

## Step 8: Robust error handling
- [ ] Ensure per-model failures never crash the request

## Step 9: Testing
- [ ] Run server and manually test upload + auto train with messy datasets

