"""
Test Dataset Context Building and Extraction
"""

import os
import django
import pandas as pd
import numpy as np

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_data_project.settings')
django.setup()

from dataapp.services.ai_assistant import build_dataset_context, _statistics_context, _correlation_context
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def create_sample_dataset():
    """Create a sample dataset for testing"""
    np.random.seed(42)
    data = {
        'age': np.random.randint(18, 80, 100),
        'income': np.random.randint(20000, 150000, 100),
        'credit_score': np.random.randint(300, 850, 100),
        'loan_amount': np.random.randint(1000, 500000, 100),
        'default': np.random.choice([0, 1], 100),
    }
    df = pd.DataFrame(data)
    # Add some missing values
    df.loc[5:8, 'income'] = np.nan
    return df


def test_dataset_context_generation():
    """Test dataset context generation"""
    print("\n[TEST 1] Dataset Context Generation")

    df = create_sample_dataset()

    context = build_dataset_context(
        df=df,
        dataset_name="test_dataset",
        target_column="default",
    )

    print(f"Dataset Name: {context['dataset_information']['dataset_name']}")
    print(f"Rows: {context['dataset_information']['rows']}")
    print(f"Columns: {context['dataset_information']['columns']}")
    print(f"Column Names: {context['dataset_information']['column_names']}")
    print(f"Target Column: {context['dataset_information']['target_column']}")
    print(f"Duplicate Rows: {context['dataset_information']['duplicate_rows']}")
    print(f"Missing Values: {context['dataset_information']['missing_values']}")

    assert context['dataset_information']['rows'] == 100
    assert context['dataset_information']['columns'] == 5
    assert 'default' in context['dataset_information']['column_names']

    print("\n[PASS] Dataset context generation PASSED")
    return True


def test_statistics_extraction():
    """Test statistics extraction"""
    print("\n[TEST 2] Statistics Extraction")

    df = create_sample_dataset()
    stats = _statistics_context(df)

    print(f"Statistics Available: {stats['available']}")
    print(f"Numeric Columns: {len(stats['numeric_statistics'])}")

    if stats['available']:
        age_stats = stats['numeric_statistics'].get('age', {})
        print(f"Sample Statistics (age): mean={age_stats.get('mean')}, median={age_stats.get('median')}")

    assert stats['available'] is True
    assert len(stats['numeric_statistics']) > 0

    print("\n[PASS] Statistics extraction PASSED")
    return True


def test_correlation_analysis():
    """Test correlation analysis"""
    print("\n[TEST 3] Correlation Analysis")

    df = create_sample_dataset()
    correlations = _correlation_context(df, target_column="default")

    print(f"Correlations Available: {correlations['available']}")
    print(f"Top Correlation Pairs: {len(correlations['top_pairs'])}")
    print(f"Target Correlations: {len(correlations['target_correlations'])}")

    assert correlations['available'] is True

    if correlations['top_pairs']:
        pair = correlations['top_pairs'][0]
        print(f"Sample Top Pair: {pair['columns']} corr={pair['correlation']}")

    print("\n[PASS] Correlation analysis PASSED")
    return True


def test_context_completeness():
    """Test that context contains all required fields"""
    print("\n[TEST 4] Context Completeness")

    df = create_sample_dataset()
    context = build_dataset_context(
        df=df,
        dataset_name="test_dataset",
        target_column="default",
        preprocessing_report={"summary": ["Test preprocessing"]},
        model_comparison_results=[{"model_name": "Test Model", "accuracy": 0.85}],
    )

    required_keys = [
        'dataset_information',
        'statistics',
        'correlation_results',
        'preprocessing',
        'model_results',
        'prediction_results',
        'visualization_results',
        'context_quality'
    ]

    for key in required_keys:
        exists = key in context
        print(f"{'PASS' if exists else 'FAIL'} {key}")
        assert exists, f"Missing key: {key}"

    print("\n[PASS] Context completeness PASSED")
    return True


if __name__ == '__main__':
    print("=" * 50)
    print("DATASET CONTEXT TESTS")
    print("=" * 50)

    results = []
    results.append(("Dataset Context Generation", test_dataset_context_generation()))
    results.append(("Statistics Extraction", test_statistics_extraction()))
    results.append(("Correlation Analysis", test_correlation_analysis()))
    results.append(("Context Completeness", test_context_completeness()))

    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"{test_name}: {status}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} tests passed")

