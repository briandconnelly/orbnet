# Orbnet Test Suite

This directory contains comprehensive tests for the orbnet package using pytest.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest configuration and shared fixtures
├── test_models.py           # Tests for Pydantic models
├── test_client.py           # Tests for OrbAPIClient class
├── test_mcp_server.py       # Tests for MCP server tools
├── test_integration.py      # Integration tests
├── test_utils.py            # Test utilities and helpers
└── README.md               # This file
```

## Test Categories

### Unit Tests
- **test_models.py**: Tests for all Pydantic models including validation, serialization, and error handling
- **test_client.py**: Tests for the OrbAPIClient class including HTTP requests, error handling, and async operations
- **test_mcp_server.py**: Tests for MCP server tools and configuration

### Integration Tests
- **test_integration.py**: Tests that verify components work together correctly
- Tests marked with `@pytest.mark.slow` may take longer to run
- Tests marked with `@pytest.mark.integration` require more complex setup

### Test Utilities
- **test_utils.py**: Helper functions for creating mock data and validating responses
- **conftest.py**: Shared pytest fixtures for common test data

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -e ".[test]"
```

### Basic Test Execution

Run all tests:
```bash
pytest
```

Run specific test files:
```bash
pytest tests/test_models.py
pytest tests/test_client.py
pytest tests/test_mcp_server.py
```

Run with verbose output:
```bash
pytest -v
```

### Using the Test Runner Script

The `run_tests.py` script provides convenient test execution options:

```bash
# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py --unit

# Run only integration tests
python run_tests.py --integration

# Run with coverage reporting
python run_tests.py --coverage

# Skip slow tests
python run_tests.py --fast

# Run tests in parallel
python run_tests.py --parallel 4

# Verbose output
python run_tests.py --verbose
```

### Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.asyncio`: Async tests (automatically handled)
- `@pytest.mark.slow`: Tests that take longer to run
- `@pytest.mark.integration`: Integration tests

Run tests excluding slow ones:
```bash
pytest -m "not slow"
```

### Coverage Reporting

Generate coverage reports:
```bash
pytest --cov=src/orbnet --cov-report=html --cov-report=term-missing
```

This creates an HTML coverage report in `htmlcov/index.html`.

## Test Fixtures

The test suite includes comprehensive fixtures in `conftest.py`:

### Data Fixtures
- `sample_scores_data`: Mock scores dataset response
- `sample_responsiveness_data`: Mock responsiveness dataset response
- `sample_web_responsiveness_data`: Mock web responsiveness dataset response
- `sample_speed_data`: Mock speed test dataset response
- `sample_all_datasets_response`: Mock response for get_all_datasets
- `sample_error_response`: Mock error response

### Mock Fixtures
- `mock_httpx_response`: Mock httpx response object
- `mock_httpx_client`: Mock httpx AsyncClient
- `mock_httpx_get`: Mock httpx.AsyncClient.get method
- `mock_httpx_client_context`: Mock httpx.AsyncClient context manager

### Configuration Fixtures
- `default_client_config`: Default client configuration for testing

## Test Utilities

The `test_utils.py` module provides helper functions:

### Mock Data Creation
- `create_mock_orb_response()`: Create mock Orb API response data
- `create_mock_error_response()`: Create mock error responses

### Validation Functions
- `assert_valid_orb_score_record()`: Validate Orb score record structure
- `assert_valid_responsiveness_record()`: Validate responsiveness record structure
- `assert_valid_web_responsiveness_record()`: Validate web responsiveness record structure
- `assert_valid_speed_record()`: Validate speed test record structure
- `validate_client_config()`: Validate client configuration

## Test Configuration

### pytest.ini
The `pytest.ini` file configures pytest with:
- Auto asyncio mode for async tests
- Test discovery patterns
- Output formatting options
- Custom markers

### Environment Variables
Tests can be configured using environment variables:
- `ORB_HOST`: Override default Orb host for testing
- `ORB_PORT`: Override default Orb port for testing

## Writing New Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Async Tests
Use `@pytest.mark.asyncio` for async test functions:
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Using Fixtures
Access fixtures by adding them as function parameters:
```python
def test_with_fixture(sample_scores_data):
    assert len(sample_scores_data) > 0
```

### Mocking
Use the provided mock fixtures or create custom mocks:
```python
def test_with_mock(mock_httpx_response):
    mock_httpx_response.json.return_value = {"test": "data"}
    # Test implementation
```

## Continuous Integration

The test suite is designed to work with CI/CD systems:

1. Install dependencies: `pip install -e ".[test]"`
2. Run tests: `pytest`
3. Generate coverage: `pytest --cov=src/orbnet --cov-report=xml`

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the package is installed in development mode: `pip install -e .`
2. **Async Test Failures**: Ensure `pytest-asyncio` is installed and `asyncio_mode = auto` is set
3. **Mock Failures**: Check that mock objects are properly configured and called
4. **Timeout Issues**: Increase timeout values for slow tests

### Debug Mode
Run tests with debug output:
```bash
pytest -v -s --tb=long
```

### Test Discovery
Check which tests would be discovered:
```bash
pytest --collect-only
```

