"""Integration tests for customers endpoints with mocked GraphDB."""

import pytest
import httpx
from unittest.mock import patch

from src.config import settings


@pytest.mark.integration
@pytest.mark.asyncio
async def test_customers_endpoint_integration(client, httpx_mock):
    """Integration test for customers endpoint with mocked HTTP calls."""
    
    mock_response = {
        "results": {
            "bindings": [
                {
                    "name": {"value": "Alice Johnson"},
                    "email": {"value": "alice@example.com"},
                    "phone": {"value": "+1555123456"}
                }
            ]
        }
    }
    
    # Mock the GraphDB SPARQL endpoint
    httpx_mock.add_response(
        method="POST",
        url=settings.graphdb_url,
        json=mock_response,
        status_code=200
    )
    
    response = client.get("/api/v1/customers/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Alice Johnson"
    assert data[0]["email"] == "alice@example.com"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_customer_details_integration(client, httpx_mock):
    """Integration test for customer details with multiple GraphDB calls."""
    
    customer_details_response = {
        "results": {
            "bindings": [
                {
                    "person": {"value": "https://static.rwpz.net/spendcast/alice"},
                    "name": {"value": "Alice Johnson"},
                    "email": {"value": "alice@example.com"},
                    "phone": {"value": "+1555123456"},
                    "birth_date": {"value": "1985-05-15"},
                    "citizenship": {"value": "CA"}
                }
            ]
        }
    }
    
    accounts_response = {
        "results": {
            "bindings": [
                {
                    "account": {"value": "https://static.rwpz.net/spendcast/alice_checking"},
                    "account_type": {"value": "https://static.rwpz.net/spendcast/schema#CheckingAccount"},
                    "balance": {"value": "2500.00"},
                    "currency": {"value": "https://static.rwpz.net/spendcast/CAD"},
                    "iban": {"value": "CA9876543210987654321"}
                }
            ]
        }
    }
    
    # Mock multiple GraphDB calls
    httpx_mock.add_response(
        method="POST",
        url=settings.graphdb_url,
        json=customer_details_response,
        status_code=200
    )
    httpx_mock.add_response(
        method="POST", 
        url=settings.graphdb_url,
        json=accounts_response,
        status_code=200
    )
    
    response = client.get("/api/v1/customers/Alice%20Johnson")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify customer details
    customer = data["customer"]
    assert customer["name"] == "Alice Johnson"
    assert customer["citizenship"] == "CA"
    
    # Verify accounts
    assert len(data["accounts"]) == 1
    assert data["accounts"][0]["balance"] == 2500.00
    assert data["total_balance"] == 2500.00


@pytest.mark.integration
@pytest.mark.asyncio
async def test_graphdb_connection_failure(client, httpx_mock):
    """Test integration behavior when GraphDB is unavailable."""
    
    # Mock a connection failure
    httpx_mock.add_exception(
        httpx.ConnectError("Connection failed")
    )
    
    response = client.get("/api/v1/customers/")
    
    assert response.status_code == 500
    data = response.json()
    assert "Failed to connect to GraphDB" in data["detail"]


@pytest.mark.integration
@pytest.mark.asyncio 
async def test_graphdb_server_error(client, httpx_mock):
    """Test integration behavior when GraphDB returns server error."""
    
    # Mock a server error from GraphDB
    httpx_mock.add_response(
        method="POST",
        url=settings.graphdb_url,
        status_code=500,
        text="Internal Server Error"
    )
    
    response = client.get("/api/v1/customers/")
    
    assert response.status_code == 500
    data = response.json()
    assert "GraphDB error" in data["detail"]


@pytest.mark.integration 
@pytest.mark.asyncio
async def test_customer_transactions_integration(client, httpx_mock):
    """Integration test for customer transactions endpoint."""
    
    transactions_response = {
        "results": {
            "bindings": [
                {
                    "transaction": {"value": "https://static.rwpz.net/spendcast/tx001"},
                    "amount": {"value": "45.99"},
                    "date": {"value": "2025-01-20T16:45:00"},
                    "status": {"value": "completed"},
                    "merchant_name": {"value": "Bookstore"}
                },
                {
                    "transaction": {"value": "https://static.rwpz.net/spendcast/tx002"},
                    "amount": {"value": "89.50"},
                    "date": {"value": "2025-01-19T12:30:00"},
                    "status": {"value": "pending"}
                }
            ]
        }
    }
    
    httpx_mock.add_response(
        method="POST",
        url=settings.graphdb_url,
        json=transactions_response,
        status_code=200
    )
    
    response = client.get("/api/v1/customers/Alice%20Johnson/transactions?limit=10&offset=0")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["customer_name"] == "Alice Johnson"
    assert len(data["transactions"]) == 2
    assert data["count"] == 2
    assert data["limit"] == 10
    assert data["offset"] == 0
    
    # Check transaction details
    tx1 = data["transactions"][0]
    assert tx1["amount"] == 45.99
    assert tx1["merchant"] == "Bookstore"
    assert tx1["status"] == "completed"
    
    tx2 = data["transactions"][1]
    assert tx2["amount"] == 89.50
    assert tx2["merchant"] == "unknown"  # No merchant_name in response
    assert tx2["status"] == "pending"


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_spending_analysis_integration(client, httpx_mock):
    """Integration test for customer spending analysis endpoint."""
    
    analysis_response = {
        "results": {
            "bindings": [
                {
                    "category_label": {"value": "Books & Education"},
                    "total_spent": {"value": "234.50"},
                    "transaction_count": {"value": "5"}
                },
                {
                    "category_label": {"value": "Entertainment"},
                    "total_spent": {"value": "156.75"},
                    "transaction_count": {"value": "3"}
                }
            ]
        }
    }
    
    httpx_mock.add_response(
        method="POST",
        url=settings.graphdb_url,
        json=analysis_response,
        status_code=200
    )
    
    response = client.get("/api/v1/customers/Alice%20Johnson/spending-analysis?year=2025")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["customer_name"] == "Alice Johnson"
    assert data["year"] == 2025
    assert len(data["categories"]) == 2
    assert data["total_spending"] == 391.25
    assert data["category_count"] == 2
    
    # Check category details
    books_category = data["categories"][0]
    assert books_category["category"] == "Books & Education"
    assert books_category["total_spent"] == 234.50
    assert books_category["transaction_count"] == 5