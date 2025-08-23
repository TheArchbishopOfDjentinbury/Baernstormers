from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
import os
from typing import Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define MCP server parameters
server_params = StdioServerParameters(
    command="uv",
    args=["run", "spendcast_mcp_server.py"],
    env=os.environ.copy(),
)

# Create FastAPI app
app = FastAPI(title="LangGraph Agent API", version="1.0.0")

# Add CORS middleware to allow frontend calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL instead of "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    success: bool
    error: Optional[str] = None


# Global variable to store initialized agent (optional optimization)
_agent = None
_tools = None


async def initialize_agent():
    """Initialize the agent and tools once"""
    global _agent, _tools

    if _agent is None:
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the connection
                    await session.initialize()
                    # Get tools
                    _tools = await load_mcp_tools(session)
                    # Create the agent
                    _agent = create_react_agent("openai:gpt-4o", _tools)
                    logger.info("Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise e


async def call_agent(message: str) -> str:
    """Call the agent with a message"""
    try:
        # Option 1: Use global agent (if initialized)
        if _agent and _tools:
            response = await _agent.ainvoke({"messages": message})
            return str(response)

        # Option 2: Create new session each time (more reliable but slower)
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                # Get tools
                tools = await load_mcp_tools(session)
                # Create and run the agent
                agent = create_react_agent("openai:gpt-4o", tools)
                agent_response = await agent.ainvoke({"messages": message})
                return str(agent_response)

    except Exception as e:
        logger.error(f"Error calling agent: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


# API Endpoints
@app.get("/")
async def root():
    return {"message": "LangGraph Agent API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent_initialized": _agent is not None}


@app.post("/chat", response_model=ChatResponse)
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


# Optional: Initialize agent on startup
@app.on_event("startup")
async def startup_event():
    """Initialize agent when the server starts"""
    try:
        await initialize_agent()
    except Exception as e:
        logger.warning(f"Could not initialize agent on startup: {e}")
        logger.info("Agent will be initialized on first request")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
