"""Test streaming chat functionality."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from main import app
from src.routers.langgraph_agent import stream_agent_response


client = TestClient(app)


class MockMessage:
    """Mock message class for testing."""

    def __init__(self, content: str):
        self.content = content


class MockChunk:
    """Mock chunk for streaming response."""

    def __init__(self, messages=None, end=False):
        if messages:
            self.data = {"messages": messages}
        elif end:
            self.data = {"__end__": True}
        else:
            self.data = {}

    def __contains__(self, key):
        return key in self.data

    def __getitem__(self, key):
        return self.data[key]


@pytest.fixture
def mock_agent():
    """Mock LangGraph agent."""
    with patch("src.routers.langgraph_agent.create_react_agent") as mock_create:
        agent = AsyncMock()
        mock_create.return_value = agent
        yield agent


@pytest.fixture
def mock_mcp_session():
    """Mock MCP session and tools."""
    with (
        patch("src.routers.langgraph_agent.stdio_client") as mock_stdio,
        patch("src.routers.langgraph_agent.ClientSession") as mock_session,
        patch("src.routers.langgraph_agent.load_mcp_tools") as mock_tools,
    ):
        # Mock the context managers
        mock_stdio.return_value.__aenter__ = AsyncMock(return_value=(None, None))
        mock_stdio.return_value.__aexit__ = AsyncMock(return_value=None)

        session = AsyncMock()
        session.initialize = AsyncMock()
        mock_session.return_value.__aenter__ = AsyncMock(return_value=session)
        mock_session.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_tools.return_value = []

        yield session


class TestStreamingEndpoint:
    """Test streaming chat endpoint."""

    def test_stream_endpoint_exists(self):
        """Test that the streaming endpoint exists."""
        response = client.post("/api/v1/agent/chat/stream", json={"message": "test"})
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_stream_agent_response_success(self, mock_agent, mock_mcp_session):
        """Test successful streaming response."""
        # Mock agent streaming response
        mock_chunks = [
            MockChunk(messages=[MockMessage("Hello")]),
            MockChunk(messages=[MockMessage(" world")]),
            MockChunk(end=True),
        ]

        async def mock_astream(input_data):
            for chunk in mock_chunks:
                yield chunk

        mock_agent.astream = mock_astream

        # Collect streaming response
        response_chunks = []
        async for chunk in stream_agent_response("test message"):
            response_chunks.append(chunk)

        # Verify response format
        assert len(response_chunks) == 3

        # Check first message chunk
        assert response_chunks[0].startswith("data: ")
        data1 = json.loads(response_chunks[0][6:].strip())
        assert data1["content"] == "Hello"
        assert data1["type"] == "message"

        # Check second message chunk
        data2 = json.loads(response_chunks[1][6:].strip())
        assert data2["content"] == " world"
        assert data2["type"] == "message"

        # Check end chunk
        data3 = json.loads(response_chunks[2][6:].strip())
        assert data3["type"] == "end"

    @pytest.mark.asyncio
    async def test_stream_agent_response_error(self, mock_mcp_session):
        """Test streaming response with error."""
        with patch("src.routers.langgraph_agent.create_react_agent") as mock_create:
            mock_create.side_effect = Exception("Test error")

            response_chunks = []
            async for chunk in stream_agent_response("test message"):
                response_chunks.append(chunk)

            # Should have one error chunk
            assert len(response_chunks) == 1
            assert response_chunks[0].startswith("data: ")

            data = json.loads(response_chunks[0][6:].strip())
            assert data["type"] == "error"
            assert "Test error" in data["error"]

    @pytest.mark.asyncio
    async def test_stream_agent_response_empty_messages(
        self, mock_agent, mock_mcp_session
    ):
        """Test streaming response with empty messages."""
        mock_chunks = [
            MockChunk(messages=[]),  # Empty messages
            MockChunk(end=True),
        ]

        async def mock_astream(input_data):
            for chunk in mock_chunks:
                yield chunk

        mock_agent.astream = mock_astream

        response_chunks = []
        async for chunk in stream_agent_response("test message"):
            response_chunks.append(chunk)

        # Should only have end chunk (no content chunks)
        assert len(response_chunks) == 1
        data = json.loads(response_chunks[0][6:].strip())
        assert data["type"] == "end"

    @pytest.mark.asyncio
    async def test_stream_agent_response_no_content(self, mock_agent, mock_mcp_session):
        """Test streaming response with messages that have no content."""

        class MockMessageNoContent:
            content = None

        mock_chunks = [
            MockChunk(messages=[MockMessageNoContent()]),
            MockChunk(end=True),
        ]

        async def mock_astream(input_data):
            for chunk in mock_chunks:
                yield chunk

        mock_agent.astream = mock_astream

        response_chunks = []
        async for chunk in stream_agent_response("test message"):
            response_chunks.append(chunk)

        # Should only have end chunk (no content chunks)
        assert len(response_chunks) == 1
        data = json.loads(response_chunks[0][6:].strip())
        assert data["type"] == "end"


class TestStreamingIntegration:
    """Integration tests for streaming endpoint."""

    @patch("src.routers.langgraph_agent.stdio_client")
    @patch("src.routers.langgraph_agent.ClientSession")
    @patch("src.routers.langgraph_agent.load_mcp_tools")
    @patch("src.routers.langgraph_agent.create_react_agent")
    def test_streaming_endpoint_response_format(
        self, mock_create, mock_tools, mock_session, mock_stdio
    ):
        """Test streaming endpoint returns correct response format."""
        # Mock the context managers
        mock_stdio.return_value.__aenter__ = AsyncMock(return_value=(None, None))
        mock_stdio.return_value.__aexit__ = AsyncMock(return_value=None)

        session = AsyncMock()
        session.initialize = AsyncMock()
        mock_session.return_value.__aenter__ = AsyncMock(return_value=session)
        mock_session.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_tools.return_value = []

        # Mock agent
        agent = AsyncMock()
        mock_create.return_value = agent

        async def mock_astream(input_data):
            yield MockChunk(messages=[MockMessage("Test response")])
            yield MockChunk(end=True)

        agent.astream = mock_astream

        # Test streaming endpoint
        response = client.post("/api/v1/agent/chat/stream", json={"message": "test"})

        # Check response headers
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")

        # Response should be streaming
        assert response.headers.get("cache-control") == "no-cache"

    def test_streaming_endpoint_validation(self):
        """Test streaming endpoint input validation."""
        # Test missing message
        response = client.post("/api/v1/agent/chat/stream", json={})
        assert response.status_code == 422

        # Test invalid JSON
        response = client.post(
            "/api/v1/agent/chat/stream",
            data="invalid json",
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 422


class TestComparisonWithNonStreaming:
    """Test that both endpoints work correctly."""

    def test_both_endpoints_exist(self):
        """Test that both streaming and non-streaming endpoints exist."""
        # Non-streaming endpoint
        response1 = client.post("/api/v1/agent/chat", json={"message": "test"})
        assert response1.status_code != 404

        # Streaming endpoint
        response2 = client.post("/api/v1/agent/chat/stream", json={"message": "test"})
        assert response2.status_code != 404

    def test_different_response_formats(self):
        """Test that endpoints return different response formats."""
        with patch("src.routers.langgraph_agent.call_agent") as mock_call:
            mock_call.return_value = "Test response"

            # Non-streaming should return JSON
            response1 = client.post("/api/v1/agent/chat", json={"message": "test"})

            assert response1.status_code == 200
            assert response1.headers["content-type"] == "application/json"

            data = response1.json()
            assert "response" in data
            assert "success" in data

        # Streaming should return text/plain
        response2 = client.post("/api/v1/agent/chat/stream", json={"message": "test"})
        assert "text/plain" in response2.headers.get("content-type", "")
