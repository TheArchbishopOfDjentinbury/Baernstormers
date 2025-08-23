# SpendCast Backend Tests

This directory contains comprehensive tests for the SpendCast Backend API.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Test fixtures and configuration
├── test_runner.py             # Custom test runner script
├── unit/                      # Unit tests
│   ├── __init__.py
│   ├── test_main.py          # Tests for main FastAPI app
│   ├── test_helloworld.py    # Tests for hello world endpoints
│   ├── test_customers.py     # Tests for customer endpoints
│   └── test_config.py        # Tests for configuration
└── integration/               # Integration tests
    ├── __init__.py
    └── test_customers_integration.py  # Integration tests with mocked GraphDB
```

## Test Categories

Tests are organized into the following markers:

- `unit` - Unit tests that test individual components in isolation
- `integration` - Integration tests that test multiple components together
- `slow` - Tests that take longer to execute
- `graphdb` - Tests that require GraphDB connection (not yet implemented)

## Running Tests

### Prerequisites

Install test dependencies:
```bash
# Install all dependencies including test ones
uv sync

# Or install manually
pip install pytest pytest-asyncio pytest-mock pytest-httpx
```

### Basic Usage

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run only unit tests
pytest -m unit

# Run only integration tests  
pytest -m integration

# Run specific test file
pytest tests/unit/test_customers.py

# Run specific test function
pytest tests/unit/test_customers.py::test_list_customers_success
```

### Using the Custom Test Runner

```bash
# Run all tests
python tests/test_runner.py

# Run only unit tests
python tests/test_runner.py --type unit

# Run with coverage report
python tests/test_runner.py --coverage

# Run with verbose output
python tests/test_runner.py -v

# Run tests in parallel (requires pytest-xdist)
python tests/test_runner.py --parallel
```

### Coverage Reports

To generate coverage reports:

```bash
# Terminal coverage report
pytest --cov=src --cov-report=term-missing

# HTML coverage report  
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser

# Both terminal and HTML
python tests/test_runner.py --coverage
```

## Test Configuration

Test configuration is defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--tb=short", 
    "--strict-markers",
    "--disable-warnings",
    "--asyncio-mode=auto"
]
```

## Test Fixtures

Common test fixtures are defined in `conftest.py`:

- `test_settings` - Test configuration settings
- `client` - FastAPI test client
- `mock_graphdb_response` - Mock GraphDB SPARQL responses
- `mock_customer_*_response` - Various customer-related mock responses
- `mock_httpx_client` - Mock HTTP client for testing external calls

## Writing New Tests

### Unit Test Example

```python
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.unit
@pytest.mark.asyncio
async def test_my_endpoint(client, mock_response_fixture):
    """Test description."""
    with patch('src.module.function', new_callable=AsyncMock) as mock_func:
        mock_func.return_value = mock_response_fixture
        
        response = client.get("/api/v1/endpoint")
        
        assert response.status_code == 200
        # Add more assertions
```

### Integration Test Example  

```python
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_scenario(client, httpx_mock):
    """Integration test description."""
    httpx_mock.add_response(
        method="POST",
        url="http://external-service/api",
        json={"result": "success"},
        status_code=200
    )
    
    response = client.get("/api/v1/endpoint")
    assert response.status_code == 200
```

## Mocking Strategy

- **Unit Tests**: Mock external dependencies (GraphDB, HTTP clients) using `unittest.mock`
- **Integration Tests**: Mock HTTP calls using `pytest-httpx` to test request/response flow
- **Fixtures**: Use pytest fixtures for reusable mock data

## Test Data

Mock responses in fixtures simulate realistic GraphDB SPARQL query results and follow the actual data structure used by the application.

## Continuous Integration

Tests can be run in CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=src --cov-report=xml
```

## Performance Testing

For performance testing of endpoints under load, consider using:
- `pytest-benchmark` for microbenchmarks
- `locust` for load testing
- `pytest-xdist` for parallel test execution

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running tests from the project root directory
2. **Async Test Issues**: Make sure to use `@pytest.mark.asyncio` for async tests
3. **Mock Not Working**: Check that patch path matches the actual import path in the module being tested

### Debug Mode

Run tests with debugging:
```bash
pytest -v -s --tb=long tests/path/to/specific_test.py
```