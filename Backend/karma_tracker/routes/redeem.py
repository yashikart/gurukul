from fastapi import APIRouter, HTTPException
from models import RedeemRequest
from database import users_col, transactions_col
from utils.tokens import apply_decay_and_expiry, now_utc
from config import TOKEN_ATTRIBUTES

router = APIRouter()

@router.post("/redeem/")
def redeem(req: RedeemRequest):
    if req.token_type not in TOKEN_ATTRIBUTES:
        raise HTTPException(status_code=400, detail="Invalid token type")
    user = users_col.find_one({"user_id": req.user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = apply_decay_and_expiry(user)
    bal = user["balances"].get(req.token_type, 0.0)
    if bal >= req.amount and req.amount > 0:
        users_col.update_one({"user_id": req.user_id}, {"$inc": {f"balances.{req.token_type}": -float(req.amount)}})
        transactions_col.insert_one({
            "user_id": req.user_id,
            "action": "redeem",
            "token": req.token_type,
            "amount": float(req.amount),
            "timestamp": now_utc()
        })
        return {"message": f"Redeemed {req.amount} {req.token_type}", "remaining": bal - req.amount}
    else:
        raise HTTPException(status_code=400, detail="Insufficient balance or invalid amount")
