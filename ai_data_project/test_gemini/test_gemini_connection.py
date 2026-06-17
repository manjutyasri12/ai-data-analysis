"""
Test Gemini API Connection and Configuration
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_data_project.settings')
django.setup()

from dataapp.services.ai_assistant import validate_gemini_setup, test_gemini_connection
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_api_key_validation():
    """Test API key validation"""
    print("\n[TEST 1] API Key Validation")
    print("-" * 50)

    validation = validate_gemini_setup()

    print(f"Package Installed: {validation['package_installed']}")
    print(f"✓ API Key Loaded: {validation['api_key_loaded']}")
    print(f"✓ Configured: {validation['configured']}")
    print(f"✓ Model: {validation['model']}")
    print(f"✓ Status: {validation['status']}")

    if validation['configured']:
        print("\n✅ API Key validation PASSED")
        return True
    else:
        print(f"\n❌ API Key validation FAILED: {validation['status']}")
        return False


def test_gemini_connectivity():
    """Test Gemini API connectivity"""
    print("\n[TEST 2] Gemini API Connectivity")
    print("-" * 50)

    result = test_gemini_connection()

    print(f"✓ Success: {result['success']}")
    print(f"✓ Status: {result['status']}")
    print(f"✓ Response: {result.get('response', 'N/A')[:100]}")

    if result['checks'].get('api_connectivity'):
        print("\n✅ Gemini connectivity PASSED")
        return True
    else:
        print("\n❌ Gemini connectivity FAILED")
        print(f"   Error: {result['checks'].get('error_message', 'Unknown error')}")
        return False


def test_package_availability():
    """Test required packages"""
    print("\n[TEST 3] Package Availability")
    print("-" * 50)

    packages = {
        'google.generativeai': 'Google Generative AI',
        'pandas': 'Pandas',
        'numpy': 'NumPy',
        'sklearn': 'Scikit-learn',
    }

    all_available = True
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"✓ {name}: Available")
        except ImportError:
            print(f"✗ {name}: NOT Available")
            all_available = False

    if all_available:
        print("\n✅ All packages AVAILABLE")
        return True
    else:
        print("\n⚠️ Some packages missing")
        return False


if __name__ == '__main__':
    print("=" * 50)
    print("GEMINI CONNECTION TESTS")
    print("=" * 50)

    results = []
    results.append(("API Key Validation", test_api_key_validation()))
    results.append(("Gemini Connectivity", test_gemini_connectivity()))
    results.append(("Package Availability", test_package_availability()))

    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} tests passed")

