"""Unit tests for customers endpoints."""

import pytest
from unittest.mock import patch, AsyncMock
import httpx


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_customers_success(client, mock_graphdb_response):
    """Test GET /api/v1/customers/ endpoint success."""
    with patch(
        "src.routers.customers.execute_sparql_query", new_callable=AsyncMock
    ) as mock_query:
        mock_query.return_value = mock_graphdb_response

        response = client.get("/api/v1/customers/")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        assert data[0]["name"] == "John Doe"
        assert data[0]["email"] == "john@example.com"
        assert data[0]["phone"] == "+1234567890"

        mock_query.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_customers_with_limit(client, mock_graphdb_response):
    """Test GET /api/v1/customers/ with limit parameter."""
    with patch(
        "src.routers.customers.execute_sparql_query", new_callable=AsyncMock
    ) as mock_query:
        mock_query.return_value = mock_graphdb_response

        response = client.get("/api/v1/customers/?limit=5")

        assert response.status_code == 200
        mock_query.assert_called_once()

        # Check that the SPARQL query contains the correct limit
        call_args = mock_query.call_args[0][0]
        assert "LIMIT 5" in call_args


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_customers_invalid_limit(client):
    """Test GET /api/v1/customers/ with invalid limit parameter."""
    response = client.get("/api/v1/customers/?limit=0")
    assert response.status_code == 422

    response = client.get("/api/v1/customers/?limit=101")
    assert response.status_code == 422


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_customer_details_success(
    client, mock_customer_details_response, mock_customer_accounts_response
):
    """Test GET /api/v1/customers/{customer_name} endpoint success."""
    with patch(
        "src.routers.customers.execute_sparql_query", new_callable=AsyncMock
    ) as mock_query:
        # First call returns customer details, second call returns accounts
        mock_query.side_effect = [
            mock_customer_details_response,
            mock_customer_accounts_response,
        ]

        response = client.get("/api/v1/customers/John%20Doe")

        assert response.status_code == 200
        data = response.json()

        # Check customer details
        customer = data["customer"]
        assert customer["name"] == "John Doe"
        assert customer["email"] == "john@example.com"
        assert customer["phone"] == "+1234567890"
        assert customer["birth_date"] == "1990-01-01"
        assert customer["citizenship"] == "US"

        # Check accounts
        accounts = data["accounts"]
        assert len(accounts) == 2
        assert accounts[0]["account_type"] == "CheckingAccount"
        assert accounts[0]["balance"] == 1500.00
        assert accounts[1]["account_type"] == "SavingsAccount"
        assert accounts[1]["balance"] == 5000.00

        # Check summary
        assert data["total_balance"] == 6500.00
        assert data["account_count"] == 2

        assert mock_query.call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_customer_details_not_found(client):
    """Test GET /api/v1/customers/{customer_name} when customer not found."""
    empty_response = {"results": {"bindings": []}}

    with patch(
        "src.routers.customers.execute_sparql_query", new_callable=AsyncMock
    ) as mock_query:
        mock_query.return_value = empty_response

        response = client.get("/api/v1/customers/NonExistent%20User")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Customer not found"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_customer_transactions_success(client, mock_transactions_response):
    """Test GET /api/v1/customers/{customer_name}/transactions endpoint success."""
    with patch(
        "src.routers.customers.execute_sparql_query", new_callable=AsyncMock
    ) as mock_query:
        mock_query.return_value = mock_transactions_response

        response = client.get("/api/v1/customers/John%20Doe/transactions")

        assert response.status_code == 200
        data = response.json()

        assert data["customer_name"] == "John Doe"
        assert len(data["transactions"]) == 2
        assert data["count"] == 2
        assert data["offset"] == 0
        assert data["limit"] == 20

        transaction = data["transactions"][0]
        assert transaction["amount"] == 25.50
        assert transaction["status"] == "completed"
        assert transaction["merchant"] == "Coffee Shop"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_customer_transactions_with_pagination(
    client, mock_transactions_response
):
    """Test GET /api/v1/customers/{customer_name}/transactions with pagination."""
    with patch(
        "src.routers.customers.execute_sparql_query", new_callable=AsyncMock
    ) as mock_query:
        mock_query.return_value = mock_transactions_response

        response = client.get(
            "/api/v1/customers/John%20Doe/transactions?limit=5&offset=10"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["offset"] == 10
        assert data["limit"] == 5

        # Check that the SPARQL query contains the correct limit and offset
        call_args = mock_query.call_args[0][0]
        assert "LIMIT 5" in call_args
        assert "OFFSET 10" in call_args


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_customer_spending_analysis_success(
    client, mock_spending_analysis_response
):
    """Test GET /api/v1/customers/{customer_name}/spending-analysis endpoint success."""
    with patch(
        "src.routers.customers.execute_sparql_query", new_callable=AsyncMock
    ) as mock_query:
        mock_query.return_value = mock_spending_analysis_response

        response = client.get("/api/v1/customers/John%20Doe/spending-analysis")

        assert response.status_code == 200
        data = response.json()

        assert data["customer_name"] == "John Doe"
        assert data["year"] == 2025
        assert len(data["categories"]) == 2
        assert data["total_spending"] == 680.75
        assert data["category_count"] == 2

        category = data["categories"][0]
        assert category["category"] == "Food & Dining"
        assert category["total_spent"] == 450.75
        assert category["transaction_count"] == 18


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_customer_spending_analysis_with_year(
    client, mock_spending_analysis_response
):
    """Test spending analysis endpoint with custom year."""
    with patch(
        "src.routers.customers.execute_sparql_query", new_callable=AsyncMock
    ) as mock_query:
        mock_query.return_value = mock_spending_analysis_response

        response = client.get(
            "/api/v1/customers/John%20Doe/spending-analysis?year=2024"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2024

        # Check that the SPARQL query contains the correct year filter
        call_args = mock_query.call_args[0][0]
        assert "2024-01-01" in call_args
        assert "2024-12-31" in call_args


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_customer_monthly_spending_success(
    client, mock_monthly_spending_response
):
    """Test GET /api/v1/customers/{customer_name}/monthly-spending endpoint success."""
    with patch(
        "src.routers.customers.execute_sparql_query", new_callable=AsyncMock
    ) as mock_query:
        mock_query.return_value = mock_monthly_spending_response

        response = client.get("/api/v1/customers/John%20Doe/monthly-spending")

        assert response.status_code == 200
        data = response.json()

        assert data["customer_name"] == "John Doe"
        assert data["year"] == 2025
        assert len(data["monthly_spending"]) == 2
        assert data["total_year_spending"] == 1201.05
        assert data["average_monthly_spending"] == 600.525

        month_data = data["monthly_spending"][0]
        assert month_data["month"] == "2025-01"
        assert month_data["total_spent"] == 680.75
        assert month_data["transaction_count"] == 26


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_sparql_query_http_error():
    """Test SPARQL query execution with HTTP error."""
    from src.routers.customers import execute_sparql_query
    from fastapi import HTTPException

    with patch("src.routers.customers.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        from unittest.mock import MagicMock

        mock_response = MagicMock()  # Use MagicMock for response, not AsyncMock

        # Create a proper mock response with status_code and text attributes
        error_response = MagicMock()
        error_response.status_code = 500
        error_response.text = "Server error"

        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=error_response
        )
        mock_response.json.return_value = {}  # Mock the json method to return a dict, not a coroutine

        # Mock the post method to return the response directly (await client.post(...))
        mock_client.post = AsyncMock(return_value=mock_response)

        # Set up the async context manager for httpx.AsyncClient()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await execute_sparql_query("SELECT * WHERE { ?s ?p ?o }")

        assert exc_info.value.status_code == 500


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_sparql_query_connection_error():
    """Test SPARQL query execution with connection error."""
    from src.routers.customers import execute_sparql_query
    from fastapi import HTTPException

    with patch("src.routers.customers.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.RequestError("Connection failed")
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await execute_sparql_query("SELECT * WHERE { ?s ?p ?o }")

        assert exc_info.value.status_code == 500
        assert "Failed to connect to GraphDB" in str(exc_info.value.detail)
