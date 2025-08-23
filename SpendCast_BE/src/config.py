"""Application configuration."""

import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    app_name: str = "Spendcast Backend API"
    app_version: str = "0.1.0"
    debug: bool = True

    # GraphDB connection (from MCP credentials)
    graphdb_url: str = os.getenv(
        "GRAPHDB_URL", "http://localhost:7200/repositories/spendcast"
    )
    graphdb_user: str = os.getenv("GRAPHDB_USER", "")
    graphdb_password: str = os.getenv("GRAPHDB_PASSWORD", "")

    # Database (fallback SQLite for local development)
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./spendcast.db")

    # CORS
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
    ]

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "spendcast-development-secret-key")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # OpenAI API configuration for LangGraph Agent
    openai_api_key: str = os.getenv("OPENAI_API_KEY")

    # MCP Server configuration
    mcp_server_command: str = os.getenv("MCP_SERVER_COMMAND", "uv")
    mcp_server_args: List[str] = ["run", "src/routers/spendcast_mcp_server.py"]

    class Config:
        env_file = ".env"


settings = Settings()
