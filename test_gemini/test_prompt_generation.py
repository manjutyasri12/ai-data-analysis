"""
Test Prompt Generation
"""

import os
import django
import pandas as pd
import numpy as np

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_data_project.settings')
django.setup()

from dataapp.services.ai_assistant import build_prompt, build_dataset_context


def create_sample_dataset():
    np.random.seed(42)
    data = {
        'age': np.random.randint(18, 80, 100),
        'income': np.random.randint(20000, 150000, 100),
        'credit_score': np.random.randint(300, 850, 100),
        'loan_amount': np.random.randint(1000, 500000, 100),
        'default': np.random.choice([0, 1], 100),
    }
    return pd.DataFrame(data)


def test_basic_prompt_generation():
    print("\n[TEST 1] Basic Prompt Generation")

    df = create_sample_dataset()
    context = build_dataset_context(df, dataset_name="test_dataset", target_column="default")

    question = "Explain this dataset"
    prompt = build_prompt(question, context)

    assert len(prompt) > 0
    assert question in prompt
    assert 'Dataset Information' in prompt or 'dataset_information' in prompt

    print("[PASS] Basic prompt generation")
    return True


def test_prompt_truncation():
    print("\n[TEST 2] Prompt Truncation")

    df = create_sample_dataset()

    large_model_results = [
        {"model_name": f"Model_{i}", "accuracy": np.random.rand()}
        for i in range(100)
    ]

    context = build_dataset_context(
        df,
        dataset_name="test_dataset",
        target_column="default",
        model_comparison_results=large_model_results,
    )

    prompt = build_prompt("Compare all models", context)

    MAX_CONTEXT_CHARS = 24000
    assert len(prompt) <= MAX_CONTEXT_CHARS

    print("[PASS] Prompt truncation")
    return True


def test_special_characters_handling():
    print("\n[TEST 3] Special Characters Handling")

    df = create_sample_dataset()
    context = build_dataset_context(df, dataset_name="test_dataset", target_column="default")

    special_questions = [
        'Explain "quoted" text',
        "What's the dataset?",
        'Use <tags> in response',
        'Characters: @#$%^&*()',
    ]

    for q in special_questions:
        prompt = build_prompt(q, context)
        assert len(prompt) > 0

    print("[PASS] Special characters")
    return True


if __name__ == '__main__':
    print("=" * 50)
    print("PROMPT GENERATION TESTS")
    print("=" * 50)

    results = []
    results.append(("Basic Prompt Generation", test_basic_prompt_generation()))
    results.append(("Prompt Truncation", test_prompt_truncation()))
    results.append(("Special Characters", test_special_characters_handling()))

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} tests passed")

