"""Unit tests for hello world endpoints."""

import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.unit
@pytest.mark.asyncio
async def test_hello_world_get(client, mock_hello_world_data):
    """Test GET /api/v1/hello endpoint."""
    with patch(
        "src.routers.helloworld.get_hello_world_data", new_callable=AsyncMock
    ) as mock_crud:
        mock_crud.return_value = mock_hello_world_data

        response = client.get("/api/v1/hello")

        assert response.status_code == 200
        data = response.json()

        assert data["message"] == "Hello from SpendCast API!"
        assert data["service"] == "Test Spendcast API"
        assert data["version"] == "0.1.0"
        assert data["status"] == "healthy"
        assert data["echo"] is None

        mock_crud.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_hello_world_post(client, mock_hello_world_data):
    """Test POST /api/v1/hello endpoint."""
    with patch(
        "src.routers.helloworld.get_hello_world_data", new_callable=AsyncMock
    ) as mock_crud:
        mock_crud.return_value = mock_hello_world_data

        test_text = "Hello from test!"
        response = client.post("/api/v1/hello", json={"text": test_text})

        assert response.status_code == 200
        data = response.json()

        assert data["message"] == "Hello from SpendCast API!"
        assert data["service"] == "Test Spendcast API"
        assert data["version"] == "0.1.0"
        assert data["status"] == "healthy"
        assert data["echo"] == f"You said: {test_text}"

        mock_crud.assert_called_once()


@pytest.mark.unit
def test_hello_world_post_invalid_request(client):
    """Test POST /api/v1/hello with invalid request body."""
    response = client.post("/api/v1/hello", json={})

    assert response.status_code == 422  # Validation error


@pytest.mark.unit
@pytest.mark.asyncio
async def test_hello_world_get_error_handling(client):
    """Test GET /api/v1/hello error handling."""
    with patch(
        "src.routers.helloworld.get_hello_world_data", new_callable=AsyncMock
    ) as mock_crud:
        mock_crud.side_effect = Exception("Database error")

        response = client.get("/api/v1/hello")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Internal server error"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_hello_world_post_error_handling(client):
    """Test POST /api/v1/hello error handling."""
    with patch(
        "src.routers.helloworld.get_hello_world_data", new_callable=AsyncMock
    ) as mock_crud:
        mock_crud.side_effect = Exception("Database error")

        response = client.post("/api/v1/hello", json={"text": "test"})

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Internal server error"
