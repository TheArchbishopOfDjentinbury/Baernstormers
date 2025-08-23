"""Unit tests for main FastAPI application."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_root_endpoint(client):
    """Test the root endpoint returns correct information."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data
    assert "description" in data
    assert "version" in data
    assert "endpoints" in data
    
    endpoints = data["endpoints"]
    expected_endpoints = ["docs", "redoc", "health", "database", "customers", "accounts", "transactions", "agent"]
    for endpoint in expected_endpoints:
        assert endpoint in endpoints


@pytest.mark.unit
def test_health_check_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


@pytest.mark.unit
def test_cors_headers(client):
    """Test that CORS headers are properly set."""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    
    assert response.status_code == 200