"""
Master Test Runner for Gemini Integration
Runs all tests and provides comprehensive report
"""

import os
import sys
import subprocess
import django

# Ensure the Django project package root (the folder that contains ai_data_project/) is on sys.path
# run_all_tests.py lives in: ai_data_project/test_gemini/
PROJECT_PACKAGE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
# PROJECT_PACKAGE_ROOT should be the directory that contains the `ai_data_project/` package
# (and therefore contains PROJECT_PACKAGE_ROOT/ai_data_project/settings.py)
if PROJECT_PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_PACKAGE_ROOT)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_data_project.settings')

django.setup()

def run_test_file(file_path):
    """Run a single test file and return results"""
    print(f"\n{'='*60}")
    print(f"Running: {os.path.basename(file_path)}")
    print(f"{'='*60}")
    
    try:
        env = os.environ.copy()
        # Make sure subprocess has the same import path so `ai_data_project` is resolvable
        env['PYTHONPATH'] = PROJECT_PACKAGE_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=PROJECT_PACKAGE_ROOT,
            env=env,
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"❌ TEST TIMEOUT after 120 seconds")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Main test runner"""
    print("\n" + "="*60)
    print("GEMINI INTEGRATION TEST SUITE")
    print("="*60)
    print(f"Django Environment: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print(f"Python Version: {sys.version}")
    
    # Test files are relative to the test runner location
    base_dir = os.path.dirname(__file__)
    test_files = [
        os.path.join(base_dir, 'test_gemini_connection.py'),
        os.path.join(base_dir, 'test_dataset_context.py'),
        os.path.join(base_dir, 'test_prompt_generation.py'),
        os.path.join(base_dir, 'test_conversation_memory.py'),
    ]

    
    results = {}
    
    for test_file in test_files:
        if os.path.exists(test_file):
            test_name = os.path.basename(test_file).replace('.py', '').replace('test_', '')
            passed = run_test_file(test_file)
            results[test_name] = passed
        else:
            print(f"⚠️ Test file not found: {test_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("TEST EXECUTION SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} test suites passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! Gemini integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️ {total_count - passed_count} test suite(s) failed.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
