from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from database import users_col, death_events_col
from utils.loka import compute_loka_assignment, create_rebirth_carryover, apply_rebirth

router = APIRouter()

class DeathEventRequest(BaseModel):
    user_id: str

@router.post("/event")
async def death_event(request: DeathEventRequest):
    """
    Compute loka assignment for a user (used by game engine).
    Stores the death event in the database for record keeping.
    """
    # Check if user exists
    user = users_col.find_one({"user_id": request.user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Compute loka assignment
    loka, description = compute_loka_assignment(user)
    
    # Create rebirth carryover
    carryover = create_rebirth_carryover(user)
    
    # Determine PaapTokens completion status
    paap_tokens = user.get("balances", {}).get("PaapTokens", {})
    if isinstance(paap_tokens, dict):
        total_paap = sum(paap_tokens.get(category, 0) for category in ["minor", "medium", "maha"])
        paap_status = "completed" if total_paap == 0 else "pursuing"
        paap_details = {
            "minor": paap_tokens.get("minor", 0),
            "medium": paap_tokens.get("medium", 0), 
            "maha": paap_tokens.get("maha", 0),
            "total": total_paap,
            "status": paap_status
        }
    else:
        paap_details = {"total": 0, "status": "completed", "minor": 0, "medium": 0, "maha": 0}
    
    # Store death event in database
    death_event_doc = {
        "user_id": request.user_id,
        "username": user.get("username", "Unknown"),
        "loka": loka,
        "description": description,
        "carryover": carryover,
        "final_balances": user.get("balances", {}),
        "paap_tokens_status": paap_details,
        "merit_score": user.get("merit_score", 0),
        "role": user.get("role", "Unknown"),
        "rebirth_count": user.get("rebirth_count", 0),
        "timestamp": datetime.now(timezone.utc),
        "status": "completed"
    }
    
    death_events_col.insert_one(death_event_doc)
    
    return {
        "status": "success",
        "user_id": request.user_id,
        "loka": loka,
        "description": description,
        "carryover": carryover,
        "paap_tokens_status": paap_details
    }
