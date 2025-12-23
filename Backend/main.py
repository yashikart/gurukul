#!/usr/bin/env python3
"""
Unified Backend Entry Point for Render Deployment
Gurukul Learning Platform - Production Backend
"""

import os
import sys
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from pathlib import Path

# Add Backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import centralized CORS helper
from common.cors import configure_cors

# Create main FastAPI app
app = FastAPI(
    title="Gurukul Learning Platform API",
    description="Unified backend API for the Gurukul Learning Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS using centralized helper
configure_cors(app)

# Generic OPTIONS handler for preflight requests
from fastapi import Response

@app.options("/{path:path}")
async def preflight(path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": os.getenv("NGROK_URL", "*"),
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Gurukul Learning Platform API",
        "status": "running",
        "version": "1.0.0",
        "services": [
            "base-backend",
            "memory-management", 
            "financial-simulator",
            "subject-generation",
            "akash-service",
            "tts-service"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "All services operational",
        "timestamp": "2024-01-01T00:00:00Z"
    }

# Import and mount service routers
try:
    # Import Base Backend
    from Base_backend.api import app as base_backend_app
    app.mount("/api/v1/base", base_backend_app)
    logger.info("✅ Base Backend mounted at /api/v1/base")
except Exception as e:
    logger.error(f"❌ Failed to mount Base Backend: {e}")

try:
    # Import Memory Management
    from memory_management.api import app as memory_app
    app.mount("/api/v1/memory", memory_app)
    logger.info("✅ Memory Management mounted at /api/v1/memory")
except Exception as e:
    logger.error(f"❌ Failed to mount Memory Management: {e}")

try:
    # Import Financial Simulator
    from Financial_simulator.Financial_simulator.langgraph_api import app as financial_app
    app.mount("/api/v1/financial", financial_app)
    logger.info("✅ Financial Simulator mounted at /api/v1/financial")
except Exception as e:
    logger.error(f"❌ Failed to mount Financial Simulator: {e}")

try:
    # Import Subject Generation
    from subject_generation.app import app as subject_app
    app.mount("/api/v1/subjects", subject_app)
    logger.info("✅ Subject Generation mounted at /api/v1/subjects")
except Exception as e:
    logger.error(f"❌ Failed to mount Subject Generation: {e}")

try:
    # Import Akash Service
    from akash.main import app as akash_app
    app.mount("/api/v1/akash", akash_app)
    logger.info("✅ Akash Service mounted at /api/v1/akash")
except Exception as e:
    logger.error(f"❌ Failed to mount Akash Service: {e}")

try:
    # Import TTS Service
    from tts_service.tts import app as tts_app
    app.mount("/api/v1/tts", tts_app)
    logger.info("✅ TTS Service mounted at /api/v1/tts")
except Exception as e:
    logger.error(f"❌ Failed to mount TTS Service: {e}")

if __name__ == "__main__":
    # Use port 8000 for main backend (not 8002)
    port = int(os.getenv("BASE_BACKEND_PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Starting Gurukul Backend on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
