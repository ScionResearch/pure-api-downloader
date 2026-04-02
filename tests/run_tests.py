"""Simple test runner for the staged Pure workflow project."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_summary(result):
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


def run_suite(module_names, verbosity=2):
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for module_name in module_names:
        suite.addTests(loader.loadTestsFromName(module_name))
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    print_summary(result)
    return result.wasSuccessful()


def run_all_tests(verbosity=2):
    print("=" * 70)
    print("RUNNING ALL TESTS")
    print("=" * 70)
    return run_suite(
        [
            "test_config",
            "test_setup_config",
            "test_pure_api_utils",
            "test_pure_discovery",
            "test_pure_approved_downloader",
        ],
        verbosity=verbosity,
    )


def run_specific_tests(test_module, verbosity=2):
    print("=" * 70)
    print(f"RUNNING {test_module.upper().replace('_', ' ')} TESTS")
    print("=" * 70)
    if not test_module.startswith("test_"):
        test_module = f"test_{test_module}"
    return run_suite([test_module], verbosity=verbosity)


def run_smoke_test():
    print("Running smoke test...")
    print("-" * 70)
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        import pure_api_utils
        import pure_discovery
        import pure_approved_downloader
        print("✓ Core modules import successfully")
    except ImportError as exc:
        print(f"✗ Module import failed: {exc}")
        return

    checks = [
        (pure_api_utils, "check_api_key"),
        (pure_api_utils, "test_api_connection"),
        (pure_discovery, "run_discovery_workflow"),
        (pure_approved_downloader, "run_approved_download_pilot"),
    ]

    passed = 0
    failed = 0
    for module, func_name in checks:
        if hasattr(module, func_name):
            print(f"✓ Function {module.__name__}.{func_name} exists")
            passed += 1
        else:
            print(f"✗ Function {module.__name__}.{func_name} missing")
            failed += 1

    print("\n" + "=" * 70)
    print(f"Smoke test completed: {passed} passed, {failed} failed")
    print("=" * 70)


def main():
    print("Pure API Downloader Test Suite")
    print("=" * 70)
    print()
    print("Available test suites:")
    print("  1. all       - Run all tests")
    print("  2. config    - Run config tests")
    print("  3. setup     - Run setup_config tests")
    print("  4. api       - Run pure_api_utils tests")
    print("  5. discovery - Run pure_discovery tests")
    print("  6. approved  - Run pure_approved_downloader tests")
    print("  7. smoke     - Quick smoke test")
    print()

    if len(sys.argv) > 1:
        choice = sys.argv[1].lower()
    else:
        try:
            choice = input("Enter your choice (1-7 or name): ").strip().lower()
        except KeyboardInterrupt:
            print("\nTest execution cancelled.")
            sys.exit(0)

    try:
        if choice in ["1", "all"]:
            success = run_all_tests()
        elif choice in ["2", "config"]:
            success = run_specific_tests("config")
        elif choice in ["3", "setup"]:
            success = run_specific_tests("setup_config")
        elif choice in ["4", "api"]:
            success = run_specific_tests("pure_api_utils")
        elif choice in ["5", "discovery"]:
            success = run_specific_tests("pure_discovery")
        elif choice in ["6", "approved"]:
            success = run_specific_tests("pure_approved_downloader")
        elif choice in ["7", "smoke"]:
            run_smoke_test()
            sys.exit(0)
        else:
            print(f"Unknown choice: {choice}")
            sys.exit(1)

        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted.")
        sys.exit(1)
    except Exception as exc:
        print(f"\nError running tests: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
