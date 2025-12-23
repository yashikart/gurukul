from fastapi import APIRouter, HTTPException
from database import users_col
from utils.tokens import apply_decay_and_expiry
from utils.merit import compute_user_merit_score
from config import TOKEN_ATTRIBUTES

router = APIRouter()

@router.get("/view-balance/{user_id}")
def view_balance(user_id: str):
    user = users_col.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = apply_decay_and_expiry(user)
    merit_score = compute_user_merit_score(user)
    return {
        "user_id": user_id,
        "role": user.get("role"),
        "balances": user.get("balances"),
        "merit_score": merit_score,
        "token_attributes": TOKEN_ATTRIBUTES
    }
