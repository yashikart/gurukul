from config import LEVEL_THRESHOLDS
def compute_user_merit_score(user_doc):
    b = user_doc["balances"]
    return b.get("DharmaPoints", 0) * 1.0 + b.get("SevaPoints", 0) * 1.2 + b.get("PunyaTokens", 0) * 3.0

def determine_role_from_merit(score):
    roles_sorted = sorted(LEVEL_THRESHOLDS.items(), key=lambda x: x[1])
    current = "learner"
    for role, thr in roles_sorted:
        if score >= thr:
            current = role
    return current
