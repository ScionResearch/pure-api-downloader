"""
Test Runner for Pure API Downloader

This script provides a convenient way to run all tests or specific test suites.

Usage:
    python run_tests.py                 # Interactive menu
    python run_tests.py all             # Run all tests
    python run_tests.py unit            # Run only unit tests
    python run_tests.py integration     # Run only integration tests
    python run_tests.py config          # Run config tests
    python run_tests.py setup           # Run setup_config tests
    python run_tests.py download        # Run download_pure_file tests
"""

import sys
import unittest
import os

# Add the current directory to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_all_tests(verbosity=2):
    """Run all test suites."""
    print("=" * 70)
    print("RUNNING ALL TESTS")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=os.path.dirname(__file__), pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    print_summary(result)
    return result.wasSuccessful()


def run_unit_tests(verbosity=2):
    """Run only unit tests (excluding integration)."""
    print("=" * 70)
    print("RUNNING UNIT TESTS")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Load specific test modules (excluding integration)
    for test_module in ['test_config', 'test_setup_config', 'test_basic', 'test_download_pure_file']:
        try:
            tests = loader.loadTestsFromName(test_module)
            suite.addTests(tests)
        except Exception as e:
            print(f"Warning: Could not load {test_module}: {e}")
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    print_summary(result)
    return result.wasSuccessful()


def run_integration_tests(verbosity=2):
    """Run only integration tests."""
    print("=" * 70)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('test_integration')
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    print_summary(result)
    return result.wasSuccessful()


def run_specific_tests(test_module, verbosity=2):
    """Run tests from a specific module."""
    print("=" * 70)
    print(f"RUNNING {test_module.upper().replace('_', ' ')} TESTS")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    
    # Handle both with and without test_ prefix
    if not test_module.startswith('test_'):
        test_module = f'test_{test_module}'
    
    suite = loader.loadTestsFromName(test_module)
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    print_summary(result)
    return result.wasSuccessful()


def print_summary(result):
    """Print test result summary."""
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run:     {result.testsRun}")
    print(f"Successes:     {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures:      {len(result.failures)}")
    print(f"Errors:        {len(result.errors)}")
    print(f"Skipped:       {len(result.skipped)}")
    
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
        print(f"Success rate:  {success_rate:.1f}%")
    
    print("=" * 70)


def main():
    """Main test runner with menu options."""

    print("Pure API Downloader Test Suite")
    print("=" * 70)
    print()
    print("Available test suites:")
    print("  1. all         - Run all tests")
    print("  2. unit        - Run unit tests only")
    print("  3. integration - Run integration tests only")
    print("  4. config      - Run config.py tests")
    print("  5. setup       - Run setup_config.py tests")
    print("  6. download    - Run download_pure_file.py tests")
    print("  7. basic       - Run basic functionality tests")
    print("  8. smoke       - Quick smoke test")
    print()

    # Check for command line arguments
    if len(sys.argv) > 1:
        choice = sys.argv[1].lower()
    else:
        try:
            choice = input("Enter your choice (1-8 or name): ").strip().lower()
        except KeyboardInterrupt:
            print("\nTest execution cancelled.")
            sys.exit(0)

    # Map choices to functions
    try:
        if choice in ['1', 'all']:
            success = run_all_tests()
        elif choice in ['2', 'unit']:
            success = run_unit_tests()
        elif choice in ['3', 'integration']:
            success = run_integration_tests()
        elif choice in ['4', 'config']:
            success = run_specific_tests('config')
        elif choice in ['5', 'setup']:
            success = run_specific_tests('setup_config')
        elif choice in ['6', 'download']:
            success = run_specific_tests('download_pure_file')
        elif choice in ['7', 'basic']:
            success = run_specific_tests('basic')
        elif choice in ['8', 'smoke']:
            run_smoke_test()
            sys.exit(0)
        else:
            print(f"Unknown choice: {choice}")
            sys.exit(1)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_smoke_test():
    """Run a quick smoke test to verify basic functionality."""
    print("Running smoke test...")
    print("-" * 70)

    # Import our module
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        import download_pure_file
        print("✓ Module import successful")
    except ImportError as e:
        print(f"✗ Module import failed: {e}")
        return

    # Test basic functions exist
    required_functions = [
        "log_debug",
        "check_api_key",
        "validate_base_url",
        "load_pure_ids_from_csv",
        "download_pure_file",
        "identify_pure_id_type",
    ]

    passed = 0
    failed = 0
    
    for func_name in required_functions:
        if hasattr(download_pure_file, func_name):
            print(f"✓ Function {func_name} exists")
            passed += 1
        else:
            print(f"✗ Function {func_name} missing")
            failed += 1

    # Test basic API key validation
    try:
        result = download_pure_file.check_api_key("test-key")
        print(f"✓ API key validation works")
        passed += 1
    except Exception as e:
        print(f"✗ API key validation failed: {e}")
        failed += 1

    # Test URL validation
    try:
        result = download_pure_file.validate_base_url("https://test.example.com/ws/api")
        print(f"✓ URL validation works")
        passed += 1
    except Exception as e:
        print(f"✗ URL validation failed: {e}")
        failed += 1

    print("\n" + "=" * 70)
    print(f"Smoke test completed: {passed} passed, {failed} failed")
    print("=" * 70)


if __name__ == "__main__":
    main()
