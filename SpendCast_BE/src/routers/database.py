"""Database connection check API router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import logging

from src.crud.database import check_database_connection, check_graphdb_connection

router = APIRouter(prefix="/api/v1", tags=["database"])

logger = logging.getLogger(__name__)


class DatabaseStatus(BaseModel):
    """Database connection status model."""

    status: str
    database_type: str
    error: str = None
    details: Dict[str, Any] = None


class DatabaseCheckResponse(BaseModel):
    """Complete database check response model."""

    overall_status: str
    databases: List[DatabaseStatus]
    timestamp: str


@router.get("/database/check", response_model=DatabaseCheckResponse)
async def check_database_connections():
    """Check all database connections (SQLAlchemy + GraphDB)."""
    logger.info("Database connection check endpoint called")

    try:
        # Check SQLAlchemy database
        sql_result = await check_database_connection()

        # Check GraphDB
        graphdb_result = await check_graphdb_connection()

        # Prepare response
        databases = [
            DatabaseStatus(
                status=sql_result["status"],
                database_type=sql_result["database_type"],
                error=sql_result.get("error"),
                details={
                    k: v
                    for k, v in sql_result.items()
                    if k not in ["status", "database_type", "error"]
                },
            ),
            DatabaseStatus(
                status=graphdb_result["status"],
                database_type=graphdb_result["database_type"],
                error=graphdb_result.get("error"),
                details={
                    k: v
                    for k, v in graphdb_result.items()
                    if k not in ["status", "database_type", "error"]
                },
            ),
        ]

        # Determine overall status
        all_connected = all(db.status == "connected" for db in databases)
        overall_status = "healthy" if all_connected else "degraded"

        from datetime import datetime

        timestamp = datetime.utcnow().isoformat() + "Z"

        return DatabaseCheckResponse(
            overall_status=overall_status, databases=databases, timestamp=timestamp
        )

    except Exception as e:
        logger.error(f"Error in database check endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/database/check/sql")
async def check_sql_database():
    """Check only SQLAlchemy database connection."""
    logger.info("SQL database check endpoint called")

    try:
        result = await check_database_connection()
        return result
    except Exception as e:
        logger.error(f"Error checking SQL database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/database/check/graphdb")
async def check_graph_database():
    """Check only GraphDB connection."""
    logger.info("GraphDB check endpoint called")

    try:
        result = await check_graphdb_connection()
        return result
    except Exception as e:
        logger.error(f"Error checking GraphDB: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
