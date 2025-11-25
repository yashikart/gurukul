"""
Memory Management API Implementation.

This module implements the FastAPI endpoints for memory storage and retrieval
with comprehensive error handling, validation, and security measures.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Union
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends, Query, Path, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError
import uvicorn

from .models import (
    MemoryCreateRequest, InteractionCreateRequest, MemoryUpdateRequest,
    MemoryChunkResponse, InteractionResponse, MemoryListResponse,
    InteractionListResponse, PersonaMemorySummary, MemorySearchResponse,
    ErrorResponse, SuccessResponse, MemoryCreateResponse, InteractionCreateResponse,
    ContentType, ImportanceLevel
)
from .database import get_memory_database, MemoryDatabase
from .auth import verify_api_key, get_current_user
from .utils import format_memory_response, format_interaction_response, paginate_results


# Ensure Backend utils is importable before importing logging_config
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..')) 

# Configure logging
from utils.logging_config import configure_logging 
logger = configure_logging("memory_management")

# Initialize FastAPI app
app = FastAPI(
    title="Memory Management API",
    description="Comprehensive API for storing, retrieving, and managing memory chunks and interactions for persona-based AI agents",
    version="1.0.0",
    docs_url="/memory/docs",
    redoc_url="/memory/redoc"
)

# Add CORS middleware (tighten via ALLOWED_ORIGINS)
import os
_allowed = os.getenv("ALLOWED_ORIGINS", "").strip()
_allowed_list = [o.strip() for o in _allowed.split(",") if o.strip()] or [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Global database instance
db: MemoryDatabase = get_memory_database()


@app.middleware("http")
async def add_request_id_middleware(request, call_next):
    """Add unique request ID for tracking."""
    request_id = str(uuid4())
    request.state.request_id = request_id

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)

    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP_ERROR",
            message=exc.detail,
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )


@app.exception_handler(PyMongoError)
async def database_exception_handler(request, exc):
    """Database error exception handler."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="DATABASE_ERROR",
            message="Internal database error occurred",
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            message="An unexpected error occurred",
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )


# Health check endpoint
@app.get("/memory/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        db._client.admin.command('ping')
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )


# Memory Storage Endpoints

@app.post(
    "/memory",
    response_model=MemoryCreateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Memory Storage"],
    summary="Store memory chunk",
    description="Store a new memory chunk with content, metadata, and persona association"
)
async def create_memory(
    request: MemoryCreateRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Store a new memory chunk.

    - **user_id**: User identifier
    - **persona_id**: Persona identifier
    - **content**: Memory content (1-10000 characters)
    - **content_type**: Type of memory content
    - **metadata**: Additional metadata including tags, importance, topic
    - **timestamp**: Optional timestamp (defaults to current time)
    """
    try:
        memory_id = db.create_memory_chunk(request)

        logger.info(f"Created memory {memory_id} for user {request.user_id}")

        return MemoryCreateResponse(
            message="Memory chunk created successfully",
            data={"memory_id": memory_id}
        )

    except PyMongoError as e:
        logger.error(f"Database error creating memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store memory chunk"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.post(
    "/memory/interaction",
    response_model=InteractionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Memory Storage"],
    summary="Store interaction",
    description="Store a new user-agent interaction with context and metadata"
)
async def create_interaction(
    request: InteractionCreateRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Store a new interaction record.

    - **user_id**: User identifier
    - **persona_id**: Persona identifier
    - **user_message**: User's message (1-5000 characters)
    - **agent_response**: Agent's response (1-10000 characters)
    - **context**: Interaction context including session, domain, intent
    - **metadata**: Additional metadata including response time, confidence
    """
    try:
        interaction_id = db.create_interaction(request)

        logger.info(f"Created interaction {interaction_id} for user {request.user_id}")

        return InteractionCreateResponse(
            message="Interaction created successfully",
            data={"interaction_id": interaction_id}
        )

    except PyMongoError as e:
        logger.error(f"Database error creating interaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store interaction"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating interaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Memory Retrieval Endpoints

@app.get(
    "/memory",
    response_model=Union[MemoryListResponse, InteractionListResponse],
    tags=["Memory Retrieval"],
    summary="Retrieve memories",
    description="Retrieve memories by persona or recent interactions with filtering options"
)
async def get_memories(
    persona: Optional[str] = Query(None, description="Persona ID to filter by"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    user_id: Optional[str] = Query(None, description="User ID to filter by"),
    content_type: Optional[List[ContentType]] = Query(None, description="Content types to filter by"),
    min_importance: Optional[ImportanceLevel] = Query(None, description="Minimum importance level"),
    recent_interactions: bool = Query(False, description="Retrieve recent interactions instead of memories"),
    current_user: str = Depends(get_current_user)
):
    """
    Retrieve memories or interactions based on query parameters.

    **For Memory Retrieval (persona specified):**
    - Returns memories for the specified persona
    - Supports filtering by content type and importance
    - Results ordered by importance and timestamp

    **For Recent Interactions (recent_interactions=true):**
    - Returns recent interactions for chain-of-thought processing
    - Results ordered chronologically (oldest first)
    - Supports user and persona filtering
    """
    try:
        if recent_interactions:
            # Retrieve recent interactions
            interactions_data = db.get_recent_interactions(
                limit=limit,
                user_id=user_id,
                persona_id=persona
            )

            interactions = [format_interaction_response(data) for data in interactions_data]

            return InteractionListResponse(
                interactions=interactions,
                total_count=len(interactions),
                page=1,
                page_size=limit,
                has_next=False,
                has_previous=False
            )

        elif persona:
            # Retrieve memories by persona
            memories_data, total_count = db.get_memories_by_persona(
                persona_id=persona,
                user_id=user_id,
                limit=limit,
                offset=offset,
                content_types=content_type,
                min_importance=min_importance
            )

            memories = [format_memory_response(data) for data in memories_data]

            page = (offset // limit) + 1
            has_next = offset + limit < total_count
            has_previous = offset > 0

            return MemoryListResponse(
                memories=memories,
                total_count=total_count,
                page=page,
                page_size=limit,
                has_next=has_next,
                has_previous=has_previous
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'persona' parameter or 'recent_interactions=true' must be specified"
            )

    except PyMongoError as e:
        logger.error(f"Database error retrieving memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memories"
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Additional Memory Retrieval Endpoints

@app.get(
    "/memory/{memory_id}",
    response_model=MemoryChunkResponse,
    tags=["Memory Retrieval"],
    summary="Get specific memory",
    description="Retrieve a specific memory chunk by its ID"
)
async def get_memory_by_id(
    memory_id: str = Path(..., description="Memory ID"),
    current_user: str = Depends(get_current_user)
):
    """Retrieve a specific memory chunk by ID."""
    try:
        memory_data = db.get_memory_by_id(memory_id)
        if not memory_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )

        return format_memory_response(memory_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get(
    "/memory/persona/{persona_id}/summary",
    response_model=PersonaMemorySummary,
    tags=["Memory Retrieval"],
    summary="Get persona memory summary",
    description="Get a summary of all memories for a specific persona"
)
async def get_persona_memory_summary(
    persona_id: str = Path(..., description="Persona ID"),
    user_id: Optional[str] = Query(None, description="User ID filter"),
    current_user: str = Depends(get_current_user)
):
    """Get memory summary for a persona."""
    try:
        summary_data = db.get_persona_memory_summary(persona_id, user_id)
        if not summary_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona not found or no memories available"
            )

        return PersonaMemorySummary(**summary_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving persona summary {persona_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get(
    "/memory/search",
    response_model=MemorySearchResponse,
    tags=["Memory Search"],
    summary="Search memories",
    description="Search memories using text query with optional filters"
)
async def search_memories(
    query: str = Query(..., min_length=1, description="Search query"),
    persona_id: Optional[str] = Query(None, description="Persona ID filter"),
    user_id: Optional[str] = Query(None, description="User ID filter"),
    content_type: Optional[List[ContentType]] = Query(None, description="Content type filter"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    current_user: str = Depends(get_current_user)
):
    """Search memories using text query."""
    try:
        start_time = time.time()

        results_data = db.search_memories(
            query=query,
            persona_id=persona_id,
            user_id=user_id,
            content_types=content_type,
            limit=limit
        )

        search_time = time.time() - start_time
        results = [format_memory_response(data) for data in results_data]

        return MemorySearchResponse(
            results=results,
            query=query,
            total_results=len(results),
            search_time=search_time,
            suggestions=[]  # Can be enhanced with search suggestions
        )

    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


# Memory Management Endpoints

@app.put(
    "/memory/{memory_id}",
    response_model=SuccessResponse,
    tags=["Memory Management"],
    summary="Update memory",
    description="Update an existing memory chunk"
)
async def update_memory(
    memory_id: str = Path(..., description="Memory ID"),
    request: MemoryUpdateRequest = ...,
    current_user: str = Depends(get_current_user)
):
    """Update an existing memory chunk."""
    try:
        success = db.update_memory_chunk(memory_id, request)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )

        return SuccessResponse(
            message="Memory updated successfully",
            data={"memory_id": memory_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update memory"
        )


@app.delete(
    "/memory/{memory_id}",
    response_model=SuccessResponse,
    tags=["Memory Management"],
    summary="Delete memory",
    description="Soft delete a memory chunk (marks as inactive)"
)
async def delete_memory(
    memory_id: str = Path(..., description="Memory ID"),
    hard_delete: bool = Query(False, description="Permanently delete (use with caution)"),
    current_user: str = Depends(get_current_user)
):
    """Delete a memory chunk (soft delete by default)."""
    try:
        success = db.delete_memory_chunk(memory_id, hard_delete=hard_delete)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )

        action = "permanently deleted" if hard_delete else "deactivated"
        return SuccessResponse(
            message=f"Memory {action} successfully",
            data={"memory_id": memory_id, "hard_delete": hard_delete}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete memory"
        )


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
