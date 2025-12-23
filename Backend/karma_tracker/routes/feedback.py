"""
Feedback Signal API Routes

This module provides API endpoints for the Karmic Feedback Engine.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
from utils.karma_feedback_engine import (
    feedback_engine, 
    compute_user_influence, 
    publish_user_feedback_signal,
    batch_publish_feedback_signals
)
from utils.stp_bridge import stp_bridge, check_stp_bridge_health
from validation_middleware import validation_dependency

router = APIRouter()

class FeedbackSignalRequest(BaseModel):
    """Request model for feedback signal computation"""
    user_id: str
    include_modules: Optional[bool] = True
    include_behavioral_bias: Optional[bool] = True

class BatchFeedbackSignalRequest(BaseModel):
    """Request model for batch feedback signal computation"""
    user_ids: List[str]
    include_modules: Optional[bool] = True
    include_behavioral_bias: Optional[bool] = True

class FeedbackSignalResponse(BaseModel):
    """Response model for feedback signal"""
    status: str
    user_id: str
    influence_data: Optional[Dict[str, Any]]
    signal_id: Optional[str] = None
    error: Optional[str] = None

class BatchFeedbackSignalResponse(BaseModel):
    """Response model for batch feedback signals"""
    status: str
    results: List[FeedbackSignalResponse]

class STPBridgeHealthResponse(BaseModel):
    """Response model for STP bridge health check"""
    status: str
    endpoint: str
    status_code: Optional[int]
    response_time: Optional[float]
    error: Optional[str] = None

@router.post("/feedback_signal", response_model=FeedbackSignalResponse)
async def compute_and_publish_feedback_signal(
    request: FeedbackSignalRequest,
    _: bool = Depends(validation_dependency)
):
    """
    Compute dynamic karmic influence and publish it as a telemetry signal.
    
    Args:
        request: Feedback signal request
        
    Returns:
        FeedbackSignalResponse: Computed influence and publication result
    """
    try:
        # Compute influence
        influence_data = compute_user_influence(request.user_id)
        
        # Publish signal
        result = await publish_user_feedback_signal(request.user_id)
        
        if result["status"] == "success":
            return FeedbackSignalResponse(
                status="success",
                user_id=request.user_id,
                influence_data=influence_data,
                signal_id=result["signal_id"]
            )
        else:
            return FeedbackSignalResponse(
                status="error",
                user_id=request.user_id,
                influence_data=influence_data,
                signal_id=None,
                error=result["error"]
            )
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing feedback signal: {str(e)}")

@router.get("/feedback_signal/{user_id}", response_model=FeedbackSignalResponse)
async def get_feedback_signal(
    user_id: str,
    include_modules: bool = True,
    include_behavioral_bias: bool = True,
    _: bool = Depends(validation_dependency)
):
    """
    Get computed karmic influence for a user without publishing.
    
    Args:
        user_id: User ID to compute influence for
        include_modules: Whether to include module aggregation
        include_behavioral_bias: Whether to include behavioral bias calculation
        
    Returns:
        FeedbackSignalResponse: Computed influence data
    """
    try:
        influence_data = compute_user_influence(user_id)
        
        return FeedbackSignalResponse(
            status="success",
            user_id=user_id,
            influence_data=influence_data,
            signal_id=None
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing feedback signal: {str(e)}")

@router.post("/feedback_signal/batch", response_model=BatchFeedbackSignalResponse)
async def batch_compute_and_publish_feedback_signals(
    request: BatchFeedbackSignalRequest,
    _: bool = Depends(validation_dependency)
):
    """
    Compute and publish feedback signals for multiple users in batch.
    
    Args:
        request: Batch feedback signal request
        
    Returns:
        BatchFeedbackSignalResponse: Results for all users
    """
    try:
        results = await batch_publish_feedback_signals(request.user_ids)
        
        response_results = []
        for result in results:
            if result["status"] == "success":
                # Get influence data for successful results
                try:
                    influence_data = compute_user_influence(result["user_id"])
                    response_results.append(FeedbackSignalResponse(
                        status="success",
                        user_id=result["user_id"],
                        influence_data=influence_data,
                        signal_id=result["signal_id"]
                    ))
                except Exception:
                    response_results.append(FeedbackSignalResponse(
                        status="partial_success",
                        user_id=result["user_id"],
                        influence_data=None,
                        signal_id=result["signal_id"],
                        error="Could not compute influence data"
                    ))
            else:
                response_results.append(FeedbackSignalResponse(
                    status="error",
                    user_id=result["user_id"],
                    influence_data=None,
                    signal_id=None,
                    error=result["error"]
                ))
        
        return BatchFeedbackSignalResponse(
            status="success",
            results=response_results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch processing: {str(e)}")

@router.get("/feedback_signal/health", response_model=STPBridgeHealthResponse)
async def check_feedback_system_health(
    _: bool = Depends(validation_dependency)
):
    """
    Check the health of the feedback system and STP bridge.
    
    Returns:
        STPBridgeHealthResponse: Health status of the system
    """
    try:
        health_data = check_stp_bridge_health()
        
        return STPBridgeHealthResponse(
            status=health_data["status"],
            endpoint=health_data["endpoint"],
            status_code=health_data.get("status_code"),
            response_time=health_data.get("response_time"),
            error=health_data.get("error")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking system health: {str(e)}")

@router.get("/feedback_signal/config")
async def get_feedback_engine_config(
    _: bool = Depends(validation_dependency)
):
    """
    Get the current configuration of the feedback engine.
    
    Returns:
        Dict with configuration data
    """
    try:
        return {
            "status": "success",
            "config": {
                "stp_bridge_url": stp_bridge.insightflow_endpoint,
                "retry_attempts": stp_bridge.retry_attempts,
                "timeout": stp_bridge.timeout,
                "enabled": stp_bridge.enabled,
                "feedback_batch_size": feedback_engine.feedback_batch_size,
                "feedback_interval": feedback_engine.feedback_interval
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting configuration: {str(e)}")