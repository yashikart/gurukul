from database import users_col
from datetime import datetime
from utils.tokens import now_utc
from config import ROLE_SEQUENCE, TOKEN_ATTRIBUTES

def create_user_if_missing(user_id: str, role: str = "learner"):
    user = users_col.find_one({"user_id": user_id})
    if user:
        return user
    
    # Initialize balances with proper structure for each token type
    balances = {}
    for token in TOKEN_ATTRIBUTES:
        if token == "PaapTokens":
            # PaapTokens should be a dictionary with severity categories
            balances[token] = {"minor": 0.0, "medium": 0.0, "maha": 0.0}
        elif token == "Rnanubandhan":
            # Rnanubandhan should be a dictionary with severity categories
            balances[token] = {"minor": 0.0, "medium": 0.0, "major": 0.0}
        else:
            # Other tokens are simple numeric values
            balances[token] = 0.0
    
    doc = {
        "user_id": user_id,
        "role": role,
        "balances": balances,
        "token_meta": {token: {"last_update": now_utc(), "created_at": now_utc()} for token in TOKEN_ATTRIBUTES},
        "last_decay": now_utc(),
        "history": [],
        "cheat_history": []  # Initialize empty cheat history for progressive punishment system
    }
    users_col.insert_one(doc)
    return doc
