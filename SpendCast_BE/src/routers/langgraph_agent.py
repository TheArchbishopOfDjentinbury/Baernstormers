"""LangGraph Agent router."""

import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
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
