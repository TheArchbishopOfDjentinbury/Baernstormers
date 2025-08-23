"""Test configuration and fixtures."""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from main import app
from src.config import Settings


@pytest.fixture
def test_settings():
    """Test settings fixture."""
    return Settings(
        app_name="Test Spendcast API",
        debug=True,
        graphdb_url="http://test.graphdb:7200/repositories/test",
        graphdb_user="test_user",
        graphdb_password="test_password",
        database_url="sqlite:///:memory:",
        secret_key="test-secret-key",
        openai_api_key="test-openai-key",
    )


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_graphdb_response():
    """Mock GraphDB SPARQL response."""
    return {
        "results": {
            "bindings": [
                {
                    "name": {"value": "John Doe"},
                    "email": {"value": "john@example.com"},
                    "phone": {"value": "+1234567890"}
                },
                {
                    "name": {"value": "Jane Smith"},
                    "email": {"value": "jane@example.com"},
                    "phone": {"value": "+1234567891"}
                }
            ]
        }
    }


@pytest.fixture
def mock_customer_details_response():
    """Mock customer details GraphDB response."""
    return {
        "results": {
            "bindings": [
                {
                    "person": {"value": "https://static.rwpz.net/spendcast/person1"},
                    "name": {"value": "John Doe"},
                    "email": {"value": "john@example.com"},
                    "phone": {"value": "+1234567890"},
                    "birth_date": {"value": "1990-01-01"},
                    "citizenship": {"value": "US"}
                }
            ]
        }
    }


@pytest.fixture
def mock_customer_accounts_response():
    """Mock customer accounts GraphDB response."""
    return {
        "results": {
            "bindings": [
                {
                    "account": {"value": "https://static.rwpz.net/spendcast/account1"},
                    "account_type": {"value": "https://static.rwpz.net/spendcast/schema#CheckingAccount"},
                    "balance": {"value": "1500.00"},
                    "currency": {"value": "https://static.rwpz.net/spendcast/CHF"},
                    "iban": {"value": "CH1234567890123456789"}
                },
                {
                    "account": {"value": "https://static.rwpz.net/spendcast/account2"},
                    "account_type": {"value": "https://static.rwpz.net/spendcast/schema#SavingsAccount"},
                    "balance": {"value": "5000.00"},
                    "currency": {"value": "https://static.rwpz.net/spendcast/CHF"}
                }
            ]
        }
    }


@pytest.fixture
def mock_transactions_response():
    """Mock transactions GraphDB response."""
    return {
        "results": {
            "bindings": [
                {
                    "transaction": {"value": "https://static.rwpz.net/spendcast/tx1"},
                    "amount": {"value": "25.50"},
                    "date": {"value": "2025-01-15T14:30:00"},
                    "status": {"value": "completed"},
                    "merchant_name": {"value": "Coffee Shop"}
                },
                {
                    "transaction": {"value": "https://static.rwpz.net/spendcast/tx2"},
                    "amount": {"value": "120.00"},
                    "date": {"value": "2025-01-14T10:15:00"},
                    "status": {"value": "completed"},
                    "merchant_name": {"value": "Grocery Store"}
                }
            ]
        }
    }


@pytest.fixture
def mock_spending_analysis_response():
    """Mock spending analysis GraphDB response."""
    return {
        "results": {
            "bindings": [
                {
                    "category_label": {"value": "Food & Dining"},
                    "total_spent": {"value": "450.75"},
                    "transaction_count": {"value": "18"}
                },
                {
                    "category_label": {"value": "Transportation"},
                    "total_spent": {"value": "230.00"},
                    "transaction_count": {"value": "8"}
                }
            ]
        }
    }


@pytest.fixture
def mock_monthly_spending_response():
    """Mock monthly spending GraphDB response."""
    return {
        "results": {
            "bindings": [
                {
                    "month": {"value": "2025-01"},
                    "total_spent": {"value": "680.75"},
                    "transaction_count": {"value": "26"}
                },
                {
                    "month": {"value": "2025-02"},
                    "total_spent": {"value": "520.30"},
                    "transaction_count": {"value": "19"}
                }
            ]
        }
    }


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient."""
    client = AsyncMock(spec=httpx.AsyncClient)
    response = AsyncMock()
    response.json = AsyncMock()
    response.raise_for_status = MagicMock()
    client.post.return_value.__aenter__.return_value = response
    return client, response


@pytest.fixture
def mock_hello_world_data():
    """Mock hello world CRUD response."""
    return {
        "message": "Hello from SpendCast API!",
        "service": "Test Spendcast API", 
        "version": "0.1.0",
        "status": "healthy"
    }