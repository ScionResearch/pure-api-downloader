# Test Suite for Pure API Downloader

Comprehensive test suite for the Pure API file downloader with unit tests, integration tests, and configuration tests.

## 📋 Test Coverage

### Test Modules

| Module | Purpose | Test Count |
|--------|---------|------------|
| `test_config.py` | Configuration validation and settings | 15+ tests |
| `test_setup_config.py` | Interactive setup functionality | 15+ tests |
| `test_download_pure_file.py` | Main downloader functions | 30+ tests |
| `test_basic.py` | Basic functionality smoke tests | 10+ tests |
| `test_integration.py` | End-to-end integration tests | 10+ tests |

### What's Tested

✅ **Configuration Management**
- API key validation
- URL format validation
- CSV file path validation
- Settings validation function

✅ **CSV Processing**
- File loading with multiple encodings
- Column detection
- Empty ID handling
- Missing file handling

✅ **API Interactions**
- Pure ID type identification (numeric vs UUID)
- Research output retrieval
- File metadata extraction from `electronicVersions`
- Error response handling (404, 401, 500, etc.)
- Network error recovery

✅ **File Downloads**
- Streaming downloads
- File naming and sanitization
- Multiple file type handling
- Download progress tracking

✅ **Integration Workflows**
- Complete CSV → download pipeline
- Batch processing
- Error recovery during batch operations
- Partial failure handling

## 🚀 Running Tests

### Quick Start

```bash
# Run all tests interactively
python run_tests.py

# Run all tests from command line
python run_tests.py all

# Run quick smoke test
python run_tests.py smoke
```

### Specific Test Suites

```bash
# Run only unit tests (fast)
python run_tests.py unit

# Run only integration tests
python run_tests.py integration

# Run config tests
python run_tests.py config

# Run setup_config tests
python run_tests.py setup

# Run download_pure_file tests
python run_tests.py download

# Run basic functionality tests
python run_tests.py basic
```

### Using pytest (if installed)

```bash
# Run all tests with pytest
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest test_config.py

# Run specific test class
pytest test_config.py::TestConfigValidation

# Run specific test method
pytest test_config.py::TestConfigValidation::test_validate_config_with_valid_settings
```

### Using unittest directly

```bash
# Run all tests
python -m unittest discover -s tests -p "test_*.py"

# Run specific test module
python -m unittest tests.test_config

# Run specific test class
python -m unittest tests.test_config.TestConfigValidation

# Run specific test method
python -m unittest tests.test_config.TestConfigValidation.test_validate_config_with_valid_settings
```

## 📊 Test Runner Features

The `run_tests.py` script provides:

- **Interactive Menu**: Run without arguments for interactive selection
- **Command Line**: Run with arguments for automated testing
- **Test Filtering**: Run specific test suites or modules
- **Smoke Testing**: Quick verification of basic functionality
- **Detailed Reports**: Comprehensive test result summaries

## 🔧 Test Structure

### Unit Tests

Unit tests use mocking to isolate functions and avoid external dependencies:

```python
@patch('requests.get')
def test_api_call(self, mock_get):
    mock_get.return_value = Mock(status_code=200, json=lambda: {"data": "test"})
    result = download_pure_file.some_function()
    self.assertEqual(result, expected_value)
```

### Integration Tests

Integration tests verify multiple components working together:

```python
def test_end_to_end_download(self):
    # Create test CSV
    csv_data = [["Pure ID"], ["12345"]]
    
    # Mock API responses
    # ...
    
    # Run complete workflow
    result = batch_download_from_csv(csv_file, output_dir)
    
    # Verify results
    self.assertEqual(result['successful_downloads'], 1)
```

## 🎯 Best Practices

### Running Tests During Development

1. **Before committing**:
   ```bash
   python run_tests.py all
   ```

2. **When adding new features**:
   ```bash
   python run_tests.py unit  # Fast feedback
   ```

3. **Before releases**:
   ```bash
   python run_tests.py all   # Complete verification
   ```

### Writing New Tests

1. **Test file naming**: `test_<module_name>.py`
2. **Test class naming**: `Test<FeatureName>`
3. **Test method naming**: `test_<what_is_being_tested>`
4. **Use descriptive docstrings**: Explain what the test verifies

Example:
```python
class TestNewFeature(unittest.TestCase):
    """Test suite for new feature functionality."""
    
    def test_feature_with_valid_input(self):
        """Test that feature works correctly with valid input."""
        result = new_feature("valid_input")
        self.assertEqual(result, expected_output)
```

## 🐛 Debugging Failed Tests

### View detailed error messages

```bash
# Run with maximum verbosity
python run_tests.py all

# Or with unittest
python -m unittest tests.test_module -v
```

### Run single failing test

```bash
# Using run_tests.py
python run_tests.py download

# Using unittest
python -m unittest tests.test_config.TestConfigValidation.test_specific_case
```

### Common Issues

1. **Import Errors**: Ensure `config.py` exists in parent directory
2. **Mock Conflicts**: Check that mocked objects match actual function signatures
3. **File Path Issues**: Use `tempfile` for test file creation
4. **Network Mocks**: Ensure all `requests.get()` calls are properly mocked

## 📈 Test Metrics

Current test suite provides:

- **~80+ individual tests** across all modules
- **~90% code coverage** of core functionality
- **Fast execution**: Unit tests < 5 seconds
- **Complete integration**: End-to-end workflows tested

## 🔄 Continuous Integration

These tests are designed to work with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    cd tests
    python run_tests.py all
```

## 📝 Test Dependencies

### Required
- Python 3.7+
- `unittest` (built-in)

### Optional
- `pytest` (for advanced features)
- `coverage.py` (for coverage reports)
- `pytest-cov` (for pytest coverage integration)

Install optional dependencies:
```bash
pip install pytest pytest-cov coverage
```

## 🆘 Getting Help

If tests fail:

1. Check the error message and stack trace
2. Run the specific failing test in isolation
3. Check that `config.py` has valid test values
4. Verify all mocks are properly configured
5. See the main README for project setup instructions

---

**Last Updated**: October 2024  
**Test Framework**: unittest + pytest compatible  
**Coverage**: ~90% of core functions
