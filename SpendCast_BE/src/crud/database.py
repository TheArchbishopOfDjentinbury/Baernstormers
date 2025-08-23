"""Database connection check CRUD operations."""

import logging
import httpx
from typing import Dict, Any
from sqlalchemy import text

from ..config import settings
from ..db import SessionLocal

logger = logging.getLogger(__name__)


async def check_database_connection() -> Dict[str, Any]:
    """Check SQLAlchemy database connection."""
    try:
        db = SessionLocal()
        # Simple query to test connection
        result = db.execute(text("SELECT 1 as test"))
        test_value = result.scalar()
        db.close()

        return {
            "status": "connected",
            "database_type": "SQLAlchemy",
            "database_url": settings.database_url.split("://")[0]
            + "://***",  # Hide credentials
            "test_query_result": test_value,
        }
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return {"status": "failed", "database_type": "SQLAlchemy", "error": str(e)}


async def check_graphdb_connection() -> Dict[str, Any]:
    """Check GraphDB connection using SPARQL query."""
    try:
        # Simple SPARQL query to test GraphDB connection
        query = """
        SELECT (COUNT(*) as ?count) WHERE {
            ?s ?p ?o .
        }
        LIMIT 1
        """

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/sparql-results+json",
        }
        data = {"query": query}
        auth = httpx.BasicAuth(settings.graphdb_user, settings.graphdb_password)

        # Use GraphDB URL directly - it's already the correct SPARQL endpoint
        # settings.graphdb_url = "http://localhost:7200/repositories/spendcast"
        sparql_url = settings.graphdb_url
        logger.info(f"Attempting GraphDB connection to: {sparql_url}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                sparql_url, headers=headers, data=data, auth=auth, timeout=10.0
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"GraphDB connection successful. Response: {result}")
            return {
                "status": "connected",
                "database_type": "GraphDB",
                "endpoint": sparql_url,
                "response": result,
                "test": "SPARQL count query successful",
            }

    except httpx.HTTPStatusError as e:
        logger.error(
            f"GraphDB HTTP error: {e.response.status_code} - {e.response.text}"
        )
        logger.error(f"Request URL was: {sparql_url}")
        logger.error(f"Request headers: {headers}")
        logger.error(f"Request data: {data}")
        return {
            "status": "failed",
            "database_type": "GraphDB",
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "attempted_url": sparql_url,
        }
    except httpx.RequestError as e:
        logger.error(f"GraphDB connection error: {e}")
        return {
            "status": "failed",
            "database_type": "GraphDB",
            "error": f"Connection error: {str(e)}",
        }
    except Exception as e:
        logger.error(f"GraphDB unexpected error: {e}")
        return {
            "status": "failed",
            "database_type": "GraphDB",
            "error": f"Unexpected error: {str(e)}",
        }
