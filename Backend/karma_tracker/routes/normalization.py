"""
Normalization API Routes

This module provides API endpoints for behavioral state normalization.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
import json
from pydantic import BaseModel
from database import karma_events_col
from validation_middleware import validation_dependency
from utils.karma_lifecycle import update_prarabdha_counter

router = APIRouter()

class StateSchema(BaseModel):
    """Schema for normalized behavioral state"""
    state_id: str
    module: str  # finance | game | gurukul | insight
    action_type: str
    weight: float
    feedback_value: float
    timestamp: str

class NormalizeStateRequest(BaseModel):
    """Request model for state normalization"""
    module: str  # finance | game | gurukul | insight
    action_type: str
    raw_value: float
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class NormalizeStateBatchRequest(BaseModel):
    """Request model for batch state normalization"""
    states: List[NormalizeStateRequest]

class UpdatePrarabdhaRequest(BaseModel):
    """Request model for updating Prarabdha karma"""
    user_id: str
    increment: float
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

def load_context_weights() -> Dict[str, Any]:
    """Load context weights from file"""
    try:
        with open("context_weights.json", "r") as f:
            return json.load(f)
    except Exception as e:
        # Return default weights if file cannot be loaded
        return {
            "default_behavior_weights": {
                "finance": 1.0,
                "game": 1.2,
                "gurukul": 1.3,
                "insight": 1.1
            }
        }

def normalize_single_state(request: NormalizeStateRequest) -> StateSchema:
    """Normalize a single state"""
    # Generate unique state ID
    state_id = str(uuid.uuid4())
    
    # Load context weights
    weights = load_context_weights()
    behavior_weights = weights.get("default_behavior_weights", {})
    
    # Apply module-specific weighting
    module_weight = behavior_weights.get(request.module, 1.0)
    
    # Apply scaling (in a real implementation, this could be more complex)
    normalized_value = request.raw_value * module_weight
    
    # Update Prarabdha karma counter if this is a karma-related action
    # This is a simplified implementation - in a real system, you would have
    # more sophisticated logic to determine how actions affect Prarabdha
    if request.module in ["finance", "game", "gurukul", "insight"]:
        try:
            # For demonstration, we'll update Prarabdha by 10% of the normalized value
            # In a real implementation, this would be based on specific karma rules
            prarabdha_increment = normalized_value * 0.1
            # Note: We would need the user_id to update Prarabdha, which isn't available here
            # This is just a placeholder to show where the integration would occur
            pass
        except Exception:
            # If we can't update Prarabdha, continue with normalization
            pass
    
    # Create normalized state
    normalized_state = StateSchema(
        state_id=state_id,
        module=request.module,
        action_type=request.action_type,
        weight=module_weight,
        feedback_value=normalized_value,
        timestamp=datetime.utcnow().isoformat()
    )
    
    return normalized_state

@router.post("/normalize_state", response_model=StateSchema)
async def normalize_state(request: NormalizeStateRequest, _: bool = Depends(validation_dependency)):
    """
    Normalize a behavioral state from any module into a unified karmic signal.
    
    Args:
        request (NormalizeStateRequest): State normalization request
        
    Returns:
        StateSchema: Normalized state
    """
    try:
        # Normalize the state
        normalized_state = normalize_single_state(request)
        
        # Log to Karma Ledger (karma_events collection)
        event_record = {
            "event_id": normalized_state.state_id,
            "event_type": "normalized_state",
            "data": {
                "module": normalized_state.module,
                "action_type": normalized_state.action_type,
                "raw_value": request.raw_value,
                "normalized_value": normalized_state.feedback_value,
                "weight": normalized_state.weight,
                "context": request.context,
                "metadata": request.metadata
            },
            "timestamp": normalized_state.timestamp,
            "source": f"normalization_api_{normalized_state.module}",
            "status": "processed",
            "created_at": datetime.utcnow()
        }
        
        # Insert into database
        karma_events_col.insert_one(event_record)
        
        return normalized_state
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error normalizing state: {str(e)}")

@router.post("/normalize_state/batch", response_model=List[StateSchema])
async def normalize_state_batch(request: NormalizeStateBatchRequest, _: bool = Depends(validation_dependency)):
    """
    Normalize multiple behavioral states from any modules into unified karmic signals.
    
    Args:
        request (NormalizeStateBatchRequest): Batch state normalization request
        
    Returns:
        List[StateSchema]: List of normalized states
    """
    try:
        normalized_states = []
        
        # Normalize each state
        for state_request in request.states:
            normalized_state = normalize_single_state(state_request)
            normalized_states.append(normalized_state)
        
        # Log all to Karma Ledger (karma_events collection)
        for normalized_state in normalized_states:
            # Find the corresponding request
            original_request = next(
                (req for req in request.states if req.action_type == normalized_state.action_type), 
                None
            )
            
            event_record = {
                "event_id": normalized_state.state_id,
                "event_type": "normalized_state",
                "data": {
                    "module": normalized_state.module,
                    "action_type": normalized_state.action_type,
                    "raw_value": original_request.raw_value if original_request else None,
                    "normalized_value": normalized_state.feedback_value,
                    "weight": normalized_state.weight,
                    "context": original_request.context if original_request else None,
                    "metadata": original_request.metadata if original_request else None
                },
                "timestamp": normalized_state.timestamp,
                "source": f"normalization_api_{normalized_state.module}",
                "status": "processed",
                "created_at": datetime.utcnow()
            }
            
            # Insert into database
            karma_events_col.insert_one(event_record)
        
        return normalized_states
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error normalizing batch states: {str(e)}")

@router.post("/update_prarabdha")
async def update_prarabdha(request: UpdatePrarabdhaRequest, _: bool = Depends(validation_dependency)):
    """
    Update the Prarabdha karma counter for a user.
    
    Args:
        request (UpdatePrarabdhaRequest): Prarabdha update request
        
    Returns:
        Dict: Update result
    """
    try:
        new_prarabdha = update_prarabdha_counter(request.user_id, request.increment)
        
        # Log to Karma Ledger (karma_events collection)
        event_record = {
            "event_id": str(uuid.uuid4()),
            "event_type": "prarabdha_update",
            "data": {
                "user_id": request.user_id,
                "increment": request.increment,
                "new_prarabdha": new_prarabdha,
                "context": request.context,
                "metadata": request.metadata
            },
            "timestamp": datetime.utcnow().isoformat(),
            "source": "normalization_api",
            "status": "processed",
            "created_at": datetime.utcnow()
        }
        
        # Insert into database
        karma_events_col.insert_one(event_record)
        
        return {
            "status": "success",
            "user_id": request.user_id,
            "previous_prarabdha": new_prarabdha - request.increment,
            "increment": request.increment,
            "new_prarabdha": new_prarabdha,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating Prarabdha: {str(e)}")
