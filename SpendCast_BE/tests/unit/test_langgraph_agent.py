"""Unit tests for the LangGraph agent router."""

import base64
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_chat_with_agent_with_audio():
    """Test the /chat endpoint with audio generation."""
    with patch(
        "src.routers.langgraph_agent.call_agent", new_callable=AsyncMock
    ) as mock_call_agent, patch(
        "src.routers.langgraph_agent.generate_audio", new_callable=AsyncMock
    ) as mock_generate_audio:
        mock_call_agent.return_value = "This is a test response."
        mock_generate_audio.return_value = b"dummy_audio_bytes"

        response = client.post(
            "/api/v1/agent/chat",
            json={"message": "Hello", "include_audio": True},
        )

        assert response.status_code == 200
        response_json = response.json()
        assert response_json["response"] == "This is a test response."
        assert response_json["success"] is True
        assert "audio_content" in response_json
        assert (
            response_json["audio_content"]
            == base64.b64encode(b"dummy_audio_bytes").decode("utf-8")
        )


def test_chat_with_agent_without_audio():
    """Test the /chat endpoint without audio generation."""
    with patch(
        "src.routers.langgraph_agent.call_agent", new_callable=AsyncMock
    ) as mock_call_agent:
        mock_call_agent.return_value = "This is a test response."

        response = client.post(
            "/api/v1/agent/chat",
            json={"message": "Hello", "include_audio": False},
        )

        assert response.status_code == 200
        response_json = response.json()
        assert response_json["response"] == "This is a test response."
        assert response_json["success"] is True
        assert response_json["audio_content"] is None
