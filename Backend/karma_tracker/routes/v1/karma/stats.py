from fastapi import APIRouter, HTTPException
from database import users_col, transactions_col, atonements_col
from utils.tokens import apply_decay_and_expiry
from utils.merit import compute_user_merit_score
from utils.paap import get_total_paap_score
from utils.loka import calculate_net_karma
from config import TOKEN_ATTRIBUTES

router = APIRouter()

@router.get("/user/{user_id}")
async def get_user_stats(user_id: str):
    """
    Get comprehensive karma statistics for a user.
    """
    user = users_col.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = apply_decay_and_expiry(user)
    merit_score = compute_user_merit_score(user)
    paap_score = get_total_paap_score(user)
    net_karma = calculate_net_karma(user)
    
    # Get action statistics
    total_actions = transactions_col.count_documents({"user_id": user_id})
    pending_atonements = atonements_col.count_documents({
        "user_id": user_id, 
        "status": "pending"
    })
    completed_atonements = atonements_col.count_documents({
        "user_id": user_id, 
        "status": "completed"
    })
    
    return {
        "status": "success",
        "user_id": user_id,
        "role": user.get("role"),
        "merit_score": merit_score,
        "paap_score": paap_score,
        "net_karma": net_karma,
        "balances": user.get("balances", {}),
        "action_stats": {
            "total_actions": total_actions,
            "pending_atonements": pending_atonements,
            "completed_atonements": completed_atonements
        },
        "token_attributes": TOKEN_ATTRIBUTES
    }

@router.get("/system")
async def get_system_stats():
    """
    Get system-wide karma statistics.
    """
    total_users = users_col.count_documents({})
    total_actions = transactions_col.count_documents({})
    total_atonements = atonements_col.count_documents({})
    
    return {
        "status": "success",
        "system_stats": {
            "total_users": total_users,
            "total_actions": total_actions,
            "total_atonements": total_atonements
        }
    }