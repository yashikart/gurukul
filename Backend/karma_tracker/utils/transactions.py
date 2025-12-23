from database import transactions_col, users_col
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def now_utc():
    return datetime.utcnow()

def log_transaction(user_id, action, reward, intent, reward_tier, punishment_name=None):
    tx = {
        "user_id": user_id,
        "action": action,
        "intent": intent,
        "reward": reward,
        "reward_tier": reward_tier,
        "timestamp": now_utc()
    }
    
    # Add punishment name if provided (for cheat transactions)
    if punishment_name:
        tx["punishment_name"] = punishment_name
    
    try:
        transactions_col.insert_one(tx)
        # Fix: Create history field if it doesn't exist, then push to it
        users_col.update_one(
            {"user_id": user_id},
            {
                "$setOnInsert": {"history": []},
                "$push": {"history": tx}
            },
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error logging transaction for user {user_id}: {str(e)}")
        # Re-raise the exception so it can be handled upstream
        raise