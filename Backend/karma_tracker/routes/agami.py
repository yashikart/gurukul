"""
Agami Karma API Routes

This module provides API endpoints for Agami (future karma) prediction.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from utils.agami_predictor import agami_predictor
from validation_middleware import validation_dependency

router = APIRouter()

class AgamiPredictionRequest(BaseModel):
    """Request model for Agami karma prediction"""
    user_id: str
    scenario: Optional[Dict[str, Any]] = None

class ContextWeightsRequest(BaseModel):
    """Request model for updating context weights"""
    context_key: str
    weights: Dict[str, float]

@router.post("/api/v1/agami/predict")
async def predict_agami_karma(request: AgamiPredictionRequest, _: bool = Depends(validation_dependency)):
    """
    Predict Agami (future) karma for a user based on current Q-learning weights.
    
    Args:
        request (AgamiPredictionRequest): Prediction request
        
    Returns:
        dict: Agami karma prediction
    """
    try:
        prediction = agami_predictor.predict_agami_karma(
            user_id=request.user_id,
            scenario=request.scenario
        )
        return {
            "status": "success",
            "prediction": prediction
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting Agami karma: {str(e)}")

@router.get("/api/v1/agami/user/{user_id}")
async def get_agami_prediction(user_id: str, _: bool = Depends(validation_dependency)):
    """
    Get Agami karma prediction for a user.
    
    Args:
        user_id (str): The ID of the user
        
    Returns:
        dict: Agami karma prediction
    """
    try:
        prediction = agami_predictor.predict_agami_karma(user_id=user_id)
        return {
            "status": "success",
            "user_id": user_id,
            "prediction": prediction
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting Agami prediction: {str(e)}")

@router.post("/api/v1/agami/context-weights")
async def update_context_weights(request: ContextWeightsRequest, _: bool = Depends(validation_dependency)):
    """
    Update context-sensitive Purushartha weights.
    
    Args:
        request (ContextWeightsRequest): Context weights update request
        
    Returns:
        dict: Update confirmation
    """
    try:
        agami_predictor.update_context_weights(
            context_key=request.context_key,
            weights=request.weights
        )
        return {
            "status": "success",
            "message": f"Context weights updated for {request.context_key}",
            "weights": request.weights
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating context weights: {str(e)}")

@router.get("/api/v1/agami/context-weights/{context_key}")
async def get_context_weights(context_key: str, _: bool = Depends(validation_dependency)):
    """
    Get context-sensitive Purushartha weights.
    
    Args:
        context_key (str): The context key
        
    Returns:
        dict: Context weights
    """
    try:
        weights = agami_predictor.get_context_weights(context_key)
        return {
            "status": "success",
            "context_key": context_key,
            "weights": weights
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting context weights: {str(e)}")

@router.get("/api/v1/agami/scenarios")
async def get_sample_scenarios(_: bool = Depends(validation_dependency)):
    """
    Get sample scenarios for Agami prediction.
    
    Returns:
        dict: Sample scenarios
    """
    scenarios = {
        "student_in_gurukul": {
            "context": {
                "environment": "gurukul",
                "role": "student",
                "goal": "learning"
            },
            "description": "Student performing Artha actions in Gurukul environment"
        },
        "warrior_in_game_realm": {
            "context": {
                "environment": "game_realm",
                "role": "warrior",
                "goal": "conquest"
            },
            "description": "Warrior performing Kama actions in Game Realm"
        },
        "merchant_in_marketplace": {
            "context": {
                "environment": "marketplace",
                "role": "merchant",
                "goal": "prosperity"
            },
            "description": "Merchant performing Artha actions in marketplace"
        }
    }
    
    return {
        "status": "success",
        "scenarios": scenarios
    }