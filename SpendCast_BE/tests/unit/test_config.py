"""Unit tests for configuration."""

import pytest
import os
from unittest.mock import patch

from src.config import Settings


@pytest.mark.unit
def test_settings_default_values():
    """Test that settings have correct default values."""
    settings = Settings()
    
    assert settings.app_name == "Spendcast Backend API"
    assert settings.app_version == "0.1.0"
    assert settings.debug is True
    assert "localhost:7200" in settings.graphdb_url
    assert "sqlite:///" in settings.database_url
    assert settings.algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30


@pytest.mark.unit
def test_settings_cors_origins():
    """Test CORS origins configuration."""
    settings = Settings()
    
    expected_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    
    for origin in expected_origins:
        assert origin in settings.allowed_origins


@pytest.mark.unit
def test_settings_from_environment():
    """Test settings loading from environment variables."""
    with patch.dict(os.environ, {
        "GRAPHDB_URL": "http://test-graphdb:7200/repositories/test",
        "GRAPHDB_USER": "test_user",
        "GRAPHDB_PASSWORD": "test_password",
        "SECRET_KEY": "test-secret-key",
        "OPENAI_API_KEY": "test-openai-key",
        "DATABASE_URL": "postgresql://test:test@localhost/test"
    }):
        settings = Settings()
        
        assert settings.graphdb_url == "http://test-graphdb:7200/repositories/test"
        assert settings.graphdb_user == "test_user"
        assert settings.graphdb_password == "test_password"
        assert settings.secret_key == "test-secret-key"
        assert settings.openai_api_key == "test-openai-key"
        assert settings.database_url == "postgresql://test:test@localhost/test"


@pytest.mark.unit
def test_mcp_server_configuration():
    """Test MCP server configuration."""
    settings = Settings()
    
    assert settings.mcp_server_command == "uv"
    assert settings.mcp_server_args == ["run", "src/routers/spendcast_mcp_server.py"]