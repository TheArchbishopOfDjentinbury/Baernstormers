"""Hello World CRUD operations."""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def get_hello_world_data() -> Dict[str, Any]:
    """Get hello world data from the database/external service."""
    logger.info("Retrieving hello world data")

    # For now, return static data
    # Later this can be connected to GraphDB or other data sources
    data = {
        "message": "Hello from Spendcast Backend!",
        "service": "spendcast-backend",
        "version": "0.1.0",
        "status": "running"
    }
    
    logger.info(f"Hello world data retrieved: {data}")
    return data
