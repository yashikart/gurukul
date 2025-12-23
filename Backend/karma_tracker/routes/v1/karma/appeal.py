from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import users_col
from utils.paap import classify_paap_action
from utils.atonement import create_atonement_plan

router = APIRouter()

class AppealRequest(BaseModel):
    user_id: str
    action: str
    context: Optional[str] = None

@router.post("/")
async def appeal_karma(request: AppealRequest):
    """
    User requests review of a Paap action and receives a prescribed prāyaśchitta plan.
    """
    # Check if user exists
    user = users_col.find_one({"user_id": request.user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Classify the action to determine Paap severity
    severity_class = classify_paap_action(request.action)
    if not severity_class:
        raise HTTPException(status_code=400, detail="Action does not qualify for appeal")
    
    # Create an atonement plan
    plan = create_atonement_plan(request.user_id, request.action, severity_class)
    if not plan:
        raise HTTPException(status_code=500, detail="Failed to create atonement plan")
    
    return {
        "status": "success",
        "message": "Appeal registered successfully",
        "plan": plan
    }

@router.get("/status/{user_id}")
async def appeal_status(user_id: str):
    """
    Shows open appeals and progress for a user.
    """
    from utils.atonement import get_user_atonement_plans
    
    plans = get_user_atonement_plans(user_id)
    
    return {
        "status": "success",
        "pending_plans": [p for p in plans if p["status"] == "pending"],
        "completed_plans": [p for p in plans if p["status"] == "completed"]
    }