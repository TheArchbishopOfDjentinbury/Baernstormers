"""Hello World API router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from src.crud.helloworld import get_hello_world_data

router = APIRouter(prefix="/api/v1", tags=["hello"])

logger = logging.getLogger(__name__)


class HelloWorldRequest(BaseModel):
    """Hello world request model."""

    text: str


class HelloWorldResponse(BaseModel):
    """Hello world response model."""

    message: str
    service: str
    version: str
    status: str
    echo: str = None


@router.get("/hello", response_model=HelloWorldResponse)
async def hello_world_get():
    """Simple hello world GET endpoint."""
    logger.info("Hello world GET endpoint called")

    try:
        # Get data from CRUD
        response_data = await get_hello_world_data()

        return HelloWorldResponse(**response_data)
    except Exception as e:
        logger.error(f"Error in hello world GET: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/hello", response_model=HelloWorldResponse)
async def hello_world_post(request: HelloWorldRequest):
    """Hello world POST endpoint with echo."""
    logger.info(f"Hello world POST endpoint called with text: {request.text}")

    try:
        # Get data from CRUD
        response_data = await get_hello_world_data()

        # Add echo of the input text
        response_data["echo"] = f"You said: {request.text}"

        return HelloWorldResponse(**response_data)
    except Exception as e:
        logger.error(f"Error in hello world POST: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
