"""LangGraph Agent router."""

import json
import logging
import os
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from ..config import settings

# Set up logging
logger = logging.getLogger(__name__)

# Define MCP server parameters
server_params = StdioServerParameters(
    command=settings.mcp_server_command,
    args=settings.mcp_server_args,
    env=os.environ.copy(),
)

router = APIRouter(
    prefix="/api/v1/agent",
    tags=["LangGraph Agent"],
    responses={404: {"description": "Not found"}},
)


# Request/Response models
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    success: bool
    error: Optional[str] = None


async def call_agent(message: str) -> str:
    """Call the agent with a message"""
    try:
        # Create a fresh session for each request to avoid ClosedResourceError
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                # Get tools
                tools = await load_mcp_tools(session)
                # Create and run the agent
                agent = create_react_agent("openai:gpt-4o", tools)

                # IMPORTANT: Keep the session alive during agent execution
                agent_response = await agent.ainvoke({"messages": message})

                # Extract just the final message content for cleaner response
                if hasattr(agent_response, "get") and "messages" in agent_response:
                    messages = agent_response["messages"]
                    if messages:
                        final_message = messages[-1]
                        if hasattr(final_message, "content"):
                            return final_message.content

                return str(agent_response)

    except Exception as e:
        logger.error(f"Error calling agent: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.get("/health")
async def agent_health_check():
    """Health check for LangGraph agent."""
    return {"status": "healthy", "service": "LangGraph Agent"}


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Chat with the LangGraph agent
    """
    try:
        logger.info(f"Received message: {request.message}")

        # Call the agent
        agent_response = await call_agent(request.message)

        logger.info(f"Agent responded successfully")

        return ChatResponse(response=agent_response, success=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        return ChatResponse(response="", success=False, error=str(e))


async def stream_agent_response(message: str) -> AsyncGenerator[str, None]:
    """Stream agent response as it's generated"""
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                agent = create_react_agent("openai:gpt-4o", tools)

                # Use astream instead of ainvoke for streaming
                async for chunk in agent.astream({"messages": message}):
                    # Extract content from the chunk based on LangGraph's structure
                    if "messages" in chunk:
                        messages = chunk["messages"]
                        if messages:
                            for msg in messages:
                                if hasattr(msg, "content") and msg.content:
                                    # Format as Server-Sent Events
                                    yield f"data: {json.dumps({'content': msg.content, 'type': 'message'})}\n\n"
                    elif "__end__" in chunk:
                        # Signal end of stream
                        yield f"data: {json.dumps({'type': 'end'})}\n\n"
                        break

    except Exception as e:
        logger.error(f"Error in streaming agent: {e}")
        yield f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"


@router.post("/chat/stream")
async def stream_chat_with_agent(request: ChatRequest):
    """
    Stream chat with the LangGraph agent using Server-Sent Events
    """
    logger.info(f"Received streaming message: {request.message}")

    return StreamingResponse(
        stream_agent_response(request.message),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8",
        },
    )
