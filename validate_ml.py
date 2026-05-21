#!/usr/bin/env python
"""
Validation script to test all ML models without running Django.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("ML Models Validation Script")
print("=" * 80)

# Test 1: Import ml_models
print("\n[1/3] Testing ml_models.py imports...")
try:
    from dataapp.services.ml_models import (
        REGRESSION_MODELS,
        CLASSIFICATION_MODELS,
        get_regression_models,
        get_classification_models,
        get_all_model_names,
        get_model
    )
    print("✓ All imports successful")
    print(f"  - Regression models: {len(REGRESSION_MODELS)}")
    print(f"  - Classification models: {len(CLASSIFICATION_MODELS)}")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Verify model names
print("\n[2/3] Verifying model names...")
try:
    reg_names = list(REGRESSION_MODELS.keys())
    clf_names = list(CLASSIFICATION_MODELS.keys())
    
    print(f"  Regression ({len(reg_names)}):")
    for name in reg_names:
        print(f"    ✓ {name}")
    
    print(f"\n  Classification ({len(clf_names)}):")
    for name in clf_names:
        print(f"    ✓ {name}")
    
    assert len(reg_names) == 6, f"Expected 6 regression models, got {len(reg_names)}"
    assert len(clf_names) == 6, f"Expected 6 classification models, got {len(clf_names)}"
    print("\n✓ All model counts verified")
except Exception as e:
    print(f"✗ Verification failed: {e}")
    sys.exit(1)

# Test 3: Test model instantiation
print("\n[3/3] Testing model instantiation...")
try:
    import numpy as np
    import pandas as pd
    from sklearn.model_selection import train_test_split
    
    # Create test data
    n_samples = 100
    X = pd.DataFrame({
        'feat1': np.random.randn(n_samples),
        'feat2': np.random.randn(n_samples),
        'feat3': np.random.randint(0, 5, n_samples)
    })
    y_reg = pd.Series(np.random.randn(n_samples))
    y_clf = pd.Series(np.random.randint(0, 2, n_samples))
    
    X_train, X_test, _, _ = train_test_split(X, y_reg, test_size=0.2, random_state=42)
    
    # Test one regression model
    print("\n  Testing Regression Models:")
    reg_model = get_model("Linear Regression", "regression")
    reg_model.fit(X_train, y_reg.iloc[:len(X_train)])
    pred_reg = reg_model.predict(X_test)
    print(f"    ✓ Linear Regression - predictions shape: {pred_reg.shape}")
    
    # Test Polynomial Regression
    poly_model = get_model("Polynomial Regression", "regression")
    poly_model.fit(X_train, y_reg.iloc[:len(X_train)])
    pred_poly = poly_model.predict(X_test)
    print(f"    ✓ Polynomial Regression - predictions shape: {pred_poly.shape}")
    
    # Test Random Forest Regressor
    rf_reg_model = get_model("Random Forest Regressor", "regression")
    rf_reg_model.fit(X_train, y_reg.iloc[:len(X_train)])
    pred_rf_reg = rf_reg_model.predict(X_test)
    print(f"    ✓ Random Forest Regressor - predictions shape: {pred_rf_reg.shape}")
    
    print("\n  Testing Classification Models:")
    # Test one classification model
    clf_model = get_model("Logistic Regression", "classification")
    clf_model.fit(X_train, y_clf.iloc[:len(X_train)])
    pred_clf = clf_model.predict(X_test)
    print(f"    ✓ Logistic Regression - predictions shape: {pred_clf.shape}")
    
    # Test Random Forest Classifier
    rf_clf_model = get_model("Random Forest Classifier", "classification")
    rf_clf_model.fit(X_train, y_clf.iloc[:len(X_train)])
    pred_rf_clf = rf_clf_model.predict(X_test)
    print(f"    ✓ Random Forest Classifier - predictions shape: {pred_rf_clf.shape}")
    
    # Test SVM
    svm_model = get_model("SVM", "classification")
    svm_model.fit(X_train, y_clf.iloc[:len(X_train)])
    pred_svm = svm_model.predict(X_test)
    print(f"    ✓ SVM - predictions shape: {pred_svm.shape}")
    
    print("\n✓ All model instantiation tests passed")
except Exception as e:
    print(f"✗ Model instantiation test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("✓✓✓ ALL VALIDATION TESTS PASSED ✓✓✓")
print("=" * 80)
print("\nML Models are ready for use!")
print(f"\nTotal Models Available:")
print(f"  - Regression: 6 models")
print(f"  - Classification: 6 models")
print(f"  - Total: 12 ML models")
