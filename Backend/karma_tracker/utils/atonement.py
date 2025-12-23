from datetime import datetime, timezone
from config import PRAYASCHITTA_MAP, ATONEMENT_REWARDS
from database import users_col, transactions_col, appeals_col, atonements_col
from bson import ObjectId
from utils.qlearning import atonement_q_learning_step
from utils.merit import compute_user_merit_score, determine_role_from_merit

def serialize_mongodb_doc(doc):
    """Helper function to serialize MongoDB documents"""
    if isinstance(doc, dict):
        return {k: serialize_mongodb_doc(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [serialize_mongodb_doc(item) for item in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    else:
        return doc

def get_prescribed_atonement(severity_class):
    """
    Get the prescribed atonement plan for a given Paap severity class.
    
    Args:
        severity_class (str): The severity class ('minor', 'medium', 'maha')
        
    Returns:
        dict: Prescribed atonement plan or None if invalid severity class
    """
    if severity_class not in PRAYASCHITTA_MAP:
        return None
    
    return PRAYASCHITTA_MAP[severity_class]

def create_atonement_plan(user_id, paap_action, severity_class):
    """
    Create an atonement plan for a user based on a Paap action.
    
    Args:
        user_id (str): The user's ID
        paap_action (str): The action that generated Paap
        severity_class (str): The severity class of the Paap
        
    Returns:
        dict: The created atonement plan
    """
    prescribed = get_prescribed_atonement(severity_class)
    if not prescribed:
        return None
    
    # Create atonement plan
    plan = {
        "user_id": user_id,
        "paap_action": paap_action,
        "severity_class": severity_class,
        "created_at": datetime.now(timezone.utc),
        "status": "pending",
        "requirements": prescribed,
        "progress": {
            "Jap": 0,
            "Tap": 0,
            "Bhakti": 0,
            "Daan": 0
        },
        "proofs": []
    }
    
    # Store the plan in the separate atonements collection
    user = users_col.find_one({"user_id": user_id})
    if not user:
        return None
    
    # Create a unique plan ID
    existing_plans = list(atonements_col.find({"user_id": user_id}))
    plan_id = f"{user_id}_{paap_action}_{len(existing_plans)}"
    plan["plan_id"] = plan_id
    
    # Store appeal in appeals collection
    appeal_record = {
        "user_id": user_id,
        "paap_action": paap_action,
        "severity_class": severity_class,
        "created_at": datetime.now(timezone.utc),
        "status": "pending"
    }
    appeals_col.insert_one(appeal_record)
    
    # Store atonement plan in atonements collection
    atonements_col.insert_one(plan)
    
    return serialize_mongodb_doc(plan)

def validate_atonement_proof(plan_id, atonement_type, amount, proof_text=None, tx_hash=None):
    """
    Validate and record proof of atonement completion.
    
    Args:
        plan_id (str): The atonement plan ID
        atonement_type (str): Type of atonement (Jap, Tap, Bhakti, Daan)
        amount (float): Amount of atonement completed
        proof_text (str, optional): Text proof of completion
        tx_hash (str, optional): Transaction hash for Daan
        
    Returns:
        tuple: (success, message, updated_plan)
    """
    # Find the plan in the atonements collection
    plan = atonements_col.find_one({"plan_id": plan_id})
    if not plan:
        return False, "Atonement plan not found", None
    
    # Validate atonement type
    if atonement_type not in ["Jap", "Tap", "Bhakti", "Daan"]:
        return False, "Invalid atonement type", serialize_mongodb_doc(plan)
    
    # For Daan, require transaction hash
    if atonement_type == "Daan" and not tx_hash:
        return False, "Transaction hash required for Daan", serialize_mongodb_doc(plan)
    
    # Record the proof
    proof = {
        "type": atonement_type,
        "amount": amount,
        "submitted_at": datetime.now(timezone.utc),
        "status": "verified"  # Auto-verify for simplicity
    }
    
    if proof_text:
        proof["text"] = proof_text
    
    if tx_hash:
        proof["tx_hash"] = tx_hash
    
    # Update the atonement plan in the atonements collection
    atonements_col.update_one(
        {"plan_id": plan_id},
        {
            "$push": {"proofs": proof},
            "$inc": {f"progress.{atonement_type}": amount}
        }
    )
    
    # Get the updated plan
    plan = atonements_col.find_one({"plan_id": plan_id})
    
    # Check if atonement is complete
    is_complete = True
    for atype, required in plan["requirements"].items():
        if plan["progress"][atype] < required:
            is_complete = False
            break
    
    if is_complete:
        # Use the dedicated completion function to handle all updates
        mark_atonement_completed(plan["user_id"], plan_id)
    
    return True, "Atonement progress updated", serialize_mongodb_doc(plan)

def get_user_atonement_plans(user_id, status=None):
    """
    Get all atonement plans for a user, optionally filtered by status.
    
    Args:
        user_id (str): The user's ID
        status (str, optional): Filter by status ('pending', 'completed')
        
    Returns:
        list: List of atonement plans
    """
    # Query the atonements collection directly
    query = {"user_id": user_id}
    if status:
        query["status"] = status
    
    plans = list(atonements_col.find(query))
    return [serialize_mongodb_doc(plan) for plan in plans]

def mark_atonement_completed(user_id: str, atonement_plan_id: str):
    """
    Mark an atonement plan as completed and apply all rewards/updates.
    This function handles the complete completion flow including:
    - Reducing PaapTokens by 50%
    - Applying Q-learning rewards
    - Recalculating merit score and role
    - Recording the completion transaction
    """
    # Get the atonement plan
    atonement = atonements_col.find_one({
        'plan_id': atonement_plan_id,
        'user_id': user_id
    })
    
    if not atonement:
        return False
    
    # Get severity class (handle both field names)
    severity_class = atonement.get('severity_class') or atonement.get('paap_class')
    if not severity_class:
        return False
    
    # Get user data
    user = users_col.find_one({'user_id': user_id})
    if not user:
        return False
    
    # Apply Q-learning rewards for atonement completion
    severity_class = atonement.get('severity_class') or atonement.get('paap_class')
    if severity_class:
        # This will add rewards to PaapTokens based on severity
        reward_value, new_role = atonement_q_learning_step(user_id, severity_class)
        
        # Record completion transaction for the reward
        if reward_value > 0:
            transactions_col.insert_one({
                'user_id': user_id,
                'type': 'atonement_completion_reward',
                'token': f'PaapTokens.{severity_class}',
                'amount': reward_value,
                'timestamp': datetime.now(timezone.utc),
                'plan_id': atonement_plan_id
            })
    
    # Mark atonement as completed
    atonements_col.update_one(
        {'plan_id': atonement_plan_id},
        {'$set': {
            'status': 'completed',
            'completed_at': datetime.now(timezone.utc)
        }}
    )
    
    return True