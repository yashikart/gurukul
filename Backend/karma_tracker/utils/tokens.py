from datetime import datetime
from database import users_col
from config import TOKEN_ATTRIBUTES
from datetime import datetime

def now_utc():
    return datetime.utcnow()

def apply_decay_and_expiry(user_doc):
    last_decay = user_doc.get("last_decay", now_utc())
    if isinstance(last_decay, str):
        last_decay = datetime.fromisoformat(last_decay)
    delta_days = (now_utc() - last_decay).total_seconds() / 86400.0
    if delta_days <= 0:
        return user_doc

    balances = user_doc["balances"]
    meta = user_doc.get("token_meta", {})

    for token, attrs in TOKEN_ATTRIBUTES.items():
        decay_rate = attrs.get("daily_decay", 0.0)
        if decay_rate > 0 and balances.get(token, 0) > 0:
            decayed = balances[token] * ((1 - decay_rate) ** delta_days)
            balances[token] = max(decayed, 0.0)

        created = meta.get(token, {}).get("created_at", now_utc())
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        expiry_days = attrs.get("expiry_days", None)
        if expiry_days:
            if (now_utc() - created).days >= expiry_days:
                balances[token] = 0.0

        meta.setdefault(token, {})["last_update"] = now_utc()

    user_doc["balances"] = balances
    user_doc["token_meta"] = meta
    user_doc["last_decay"] = now_utc()

    users_col.update_one({"user_id": user_doc["user_id"]}, {"$set": {
        "balances": balances,
        "token_meta": meta,
        "last_decay": user_doc["last_decay"]
    }})
    return user_doc
