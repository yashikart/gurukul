#!/usr/bin/env python3
"""
InsightFlow Stub Endpoint

Simple stub to receive karmic feedback signals for testing purposes.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
import json
from datetime import datetime

app = FastAPI(title="InsightFlow Stub", description="Stub endpoint for receiving karmic feedback signals")

class SignalPayload(BaseModel):
    """Signal payload model"""
    transmission_id: str
    source: str
    signal: Dict[str, Any]
    timestamp: str

class HealthCheckPayload(BaseModel):
    """Health check payload model"""
    transmission_id: str
    source: str
    type: str
    timestamp: str

RECEIVED_SIGNALS = []

@app.post("/api/v1/insightflow/receive")
async def receive_karmic_signal(payload: SignalPayload):
    """
    Receive karmic feedback signal from KarmaChain
    
    Args:
        payload: Karmic signal payload
        
    Returns:
        Dict with confirmation
    """
    print(f"[{datetime.now().isoformat()}] Received signal from {payload.source}")
    print(f"  Transmission ID: {payload.transmission_id}")
    print(f"  Signal ID: {payload.signal.get('signal_id')}")
    print(f"  User ID: {payload.signal.get('user_id')}")
    print(f"  Timestamp: {payload.timestamp}")
    
    # Store the received signal
    RECEIVED_SIGNALS.append(payload.dict())
    
    return {
        "status": "received",
        "transmission_id": payload.transmission_id,
        "message": "Karmic signal received successfully",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/insightflow/health")
async def health_check(payload: HealthCheckPayload):
    """
    Health check endpoint
    
    Args:
        payload: Health check payload
        
    Returns:
        Dict with health status
    """
    print(f"[{datetime.now().isoformat()}] Health check from {payload.source}")
    
    return {
        "status": "healthy",
        "transmission_id": payload.transmission_id,
        "message": "InsightFlow stub is healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/insightflow/signals")
async def get_received_signals():
    """
    Get all received signals
    
    Returns:
        List of received signals
    """
    return {
        "status": "success",
        "count": len(RECEIVED_SIGNALS),
        "signals": RECEIVED_SIGNALS
    }

@app.delete("/api/v1/insightflow/signals")
async def clear_received_signals():
    """
    Clear all received signals
    
    Returns:
        Confirmation
    """
    global RECEIVED_SIGNALS
    count = len(RECEIVED_SIGNALS)
    RECEIVED_SIGNALS = []
    
    return {
        "status": "success",
        "message": f"Cleared {count} signals",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check_endpoint():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "insightflow_stub"}

if __name__ == "__main__":
    print("Starting InsightFlow Stub Server...")
    print("Endpoints available:")
    print("  POST /api/v1/insightflow/receive - Receive karmic signals")
    print("  POST /api/v1/insightflow/health - Health check")
    print("  GET /api/v1/insightflow/signals - Get received signals")
    print("  DELETE /api/v1/insightflow/signals - Clear received signals")
    print("  GET /health - Health check")
    print("\nServer starting on http://localhost:8001")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)