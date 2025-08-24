"""LangGraph Agent router."""

import base64
import json
import logging
import os
from typing import AsyncGenerator, Optional

import openai
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from pydantic import BaseModel
from io import BytesIO

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


class ChatRequest(BaseModel):
    message: str
    include_audio: bool = False
    response_as_audio: bool = False


class ChatResponse(BaseModel):
    response: str
    success: bool
    error: Optional[str] = None
    audio_content: Optional[str] = None


class PodcastRequest(BaseModel):
    pass


class PodcastResponse(BaseModel):
    response: str  # Base64 encoded audo of the podcast
    success: bool


preprompt = """You are a useful chat agent for PostFinance private clients.
You are currently talking to Jeanine Marie Blumenthal, with Customer ID: 76178901.
You are cheerful and warm, and give SHORT and concise answers.
Sometimes you make some jokes.

All SparQL queries MUST start with:
```
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>
```
otherwise, the queries will not work!

Here you can find some example queries:


Find Customer Transactions
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?transaction ?amount ?date ?merchant ?payer_type WHERE {
  # Find the customer
  ?person exs:hasName "CUSTOMER NAME" .
  
  # Get their accounts
  ?person exs:hasAccount ?account .
  ?account a ?payer_type .
  
  # Find transactions where the account is a payer
  ?transaction a exs:FinancialTransaction .
  ?transaction exs:hasParticipant ?payerRole .
  ?payerRole a exs:Payer .
  ?payerRole exs:isPlayedBy ?account .
  
  # Get transaction details
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount .
  ?transaction exs:hasTransactionDate ?date .
  
  # Get merchant information (payee)
  ?transaction exs:hasParticipant ?payeeRole .
  ?payeeRole a exs:Payee .
  ?payeeRole exs:isPlayedBy ?merchant .
  ?merchant rdfs:label ?merchant_label .
}
```

Find Transactions Through Payment Cards
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?transaction ?amount ?date ?card_type ?linked_account WHERE {
  ?person exs:hasName "CUSTOMER NAME" .
  ?card exs:hasCardHolder ?cardHolderRole .
  ?cardHolderRole exs:isPlayedBy ?person .
  ?card a ?card_type .
  ?card exs:linkedAccount ?linked_account .
  
  # Find transactions where the linked account is a payer
  ?transaction a exs:FinancialTransaction .
  ?transaction exs:hasParticipant ?payerRole .
  ?payerRole a exs:Payer .
  ?payerRole exs:isPlayedBy ?linked_account .
  
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount .
  ?transaction exs:hasTransactionDate ?date .
}
```

Get Customer Account Summary
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?account ?type ?balance ?currency WHERE {
  ?account a ?account_type .
  ?account exs:hasAccountHolder ?holder_role .
  ?holder_role exs:isPlayedBy ?person .
  ?person exs:hasName "CUSTOMER NAME" .
  ?account exs:hasInitialBalance ?balance .
  ?account exs:hasCurrency ?currency .
  VALUES ?account_type { exs:CheckingAccount exs:SavingsAccount exs:CreditCard exs:Retirement3A }
}
```

Get spendings for a time period
```graphql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT (SUM(?amount) AS ?total_spent) WHERE {
  # Get Jeanine's accounts and cards
  ?customer exs:hasName "Jeanine Marie Blumenthal" .
  {
    ?customer exs:hasAccount ?account .
    ?transaction a exs:FinancialTransaction ;
      exs:hasParticipant ?payerRole .
    ?payerRole a exs:Payer ;
      exs:isPlayedBy ?account .
  }
  UNION
  {
    ?customer exs:hasPaymentCard ?card .
    ?card exs:linkedAccount ?linked_account .
    ?transaction a exs:FinancialTransaction ;
      exs:hasParticipant ?payerRole .
    ?payerRole a exs:Payer ;
      exs:isPlayedBy ?linked_account .
  }
  
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount .
  ?transaction exs:hasTransactionDate ?date .
  FILTER(?date >= "2025-01-01"^^xsd:date && ?date <= "2025-01-31"^^xsd:date)
}
```
"""


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
                agent = create_react_agent("openai:gpt-4.1", tools, prompt=preprompt)

                # IMPORTANT: Keep the session alive during agent execution
                agent_response = await agent.ainvoke(
                    {"messages": [HumanMessage(content=message)]}
                )

                # Extract just the final message content for cleaner response
                if messages := agent_response.get("messages"):
                    final_message = messages[-1]
                    if hasattr(final_message, "content"):
                        return final_message.content

                return str(agent_response)

    except Exception as e:
        logger.error(f"Error calling agent: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


async def generate_audio(text: str) -> bytes:
    """Generate audio from text using OpenAI's TTS model."""
    try:
        client = openai.AsyncOpenAI()
        response = await client.audio.speech.create(
            model="tts-1", voice="alloy", input=text
        )
        return response.content
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        raise HTTPException(status_code=500, detail=f"Audio generation error: {str(e)}")


async def transcribe_audio(audio_base64: str) -> str:
    """Given an MP3 encoded in base64, transcribe the text."""
    try:
        client = openai.AsyncOpenAI()
        # the input from the user is an audio recording
        audio_bytes = base64.b64decode(audio_base64)
        audio_file = BytesIO(audio_bytes)
        audio_file.name = "user_voice.webm"  # openai needs a name to infer the format
        transcription = await client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe", file=audio_file, response_format="text"
        )
        return transcription
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(
            status_code=500, detail=f"Audio transcription error: {str(e)}"
        )


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

        if request.include_audio:
            request.message = await transcribe_audio(request.message)

        # Call the agent
        agent_response = await call_agent(request.message)

        audio_content = None
        # the user expects text AND audio as a response
        if request.response_as_audio:
            logger.info("Generating audio for the response.")
            audio_bytes = await generate_audio(agent_response)
            audio_content = base64.b64encode(audio_bytes).decode("utf-8")
            logger.info("Audio generated successfully.")

        logger.info("Agent responded successfully")

        return ChatResponse(
            response=agent_response, success=True, audio_content=audio_content
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        return ChatResponse(response="", success=False, error=str(e))


@router.get("/podcast", response_model=PodcastResponse)
async def generate_podcast(request: PodcastRequest):
    podcast_prompt = """You are tasked to generate a podcast for the user about their finances
    during the current year (2025). The podcast should last between 3 and 5 minutes when reading
    it outloud. You should cover the following topics (not required to cover them in order):
        - The current balances of all of the accounts.
        - The total spending in rent.
        - The total spending in transport (car gas, public transport, ...).
        - The total spending in food, and in which stores did you buy the most food.
        - Mention the stores where the user bought last year (2024) but hasn't yet been in 2025.
        - Given all the discussed above, generate some saving tips for the user and give a
        comment on their economical situation.
    The style of the podcast should be cheerful, and you should make some jokes along the way
    to make it easier for the user to follow (especially swiss-related jokes).

    If you make a query to the database and it fails, just try again without telling the user. If it fails again, just skip that part of the podcast. Do not mention any failures to the end user!
    """
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                # Get tools
                tools = await load_mcp_tools(session)
                # Create and run the agent
                agent = create_react_agent("openai:gpt-4.1", tools, prompt=preprompt)

                # IMPORTANT: Keep the session alive during agent execution
                agent_response = await agent.ainvoke(
                    {"messages": [SystemMessage(content=podcast_prompt)]}
                )

                # Extract just the final message content for cleaner response
                if messages := agent_response.get("messages"):
                    final_message = messages[-1]
                    if hasattr(final_message, "content"):
                        podcast_text = final_message.content

                audio_bytes = await generate_audio(podcast_text)
                audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
                return PodcastResponse(response=audio_base64, success=True)
    except Exception as e:
        logger.error(f"Error calling agent: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


async def stream_agent_response(message: str) -> AsyncGenerator[str, None]:
    """Stream agent response as it's generated"""
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                agent = create_react_agent("openai:gpt-4.1", tools)

                # Use astream instead of ainvoke for streaming
                async for token, metadata in agent.astream(
                    {"messages": [HumanMessage(content=message)]},
                    stream_mode="messages",
                ):
                    if metadata.get("langgraph_node") == "agent":
                        if hasattr(token, "content") and token.content:
                            # Format as Server-Sent Events
                            yield f"data: {json.dumps({'content': token.content, 'type': 'message'})}\n\n"

        # Signal end of stream
        yield f"data: {json.dumps({'type': 'end'})}\n\n"

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
