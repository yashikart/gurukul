from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from database import users_col
from utils.tokens import apply_decay_and_expiry, now_utc
from utils.merit import compute_user_merit_score, determine_role_from_merit
from utils.transactions import log_transaction
from utils.qlearning import q_learning_step
from utils.utils_user import create_user_if_missing
from utils.paap import classify_paap_action, apply_paap_tokens
from utils.atonement import create_atonement_plan
from utils.rnanubandhan import rnanubandhan_manager  # Import Rnanubandhan manager
from config import ROLE_SEQUENCE, ACTIONS, INTENT_MAP, REWARD_MAP, CHEAT_PUNISHMENT_LEVELS, CHEAT_PUNISHMENT_RESET_DAYS
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class LogActionRequest(BaseModel):
    user_id: str
    action: str
    role: str
    note: Optional[str] = None
    context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    # Add fields for Rnanubandhan relationships
    affected_user_id: Optional[str] = None
    relationship_description: Optional[str] = None

@router.post("/")
def log_action(req: LogActionRequest):
    try:
        if req.role not in ROLE_SEQUENCE:
            raise HTTPException(status_code=400, detail="Invalid role.")
        if req.action not in ACTIONS:
            raise HTTPException(status_code=400, detail="Invalid action.")

        # Ensure user exists
        user = users_col.find_one({"user_id": req.user_id})
        if not user:
            user = create_user_if_missing(req.user_id, req.role)

        # Apply decay/expiry
        user = apply_decay_and_expiry(user)

        # Handle cheat action with progressive punishment
        if req.action == "cheat":
            # Get user's cheat history or initialize if it doesn't exist
            cheat_history = user.get("cheat_history", [])
            current_time = now_utc()
            reset_period = timedelta(days=CHEAT_PUNISHMENT_RESET_DAYS)
            
            # Filter out old cheat attempts beyond the reset period
            recent_cheats = [ch for ch in cheat_history if current_time - ch["timestamp"] <= reset_period]
            
            # Determine cheat level (number of recent cheats + 1 for current cheat)
            cheat_level = len(recent_cheats) + 1
            
            # Get appropriate punishment
            punishment = CHEAT_PUNISHMENT_LEVELS.get(cheat_level, CHEAT_PUNISHMENT_LEVELS["default"])
            reward_value = punishment["value"]
            token = punishment["token"]
            punishment_name = punishment["name"]
            
            # Record current cheat attempt
            recent_cheats.append({"timestamp": current_time, "punishment_level": cheat_level, "value": reward_value})
            
            # Q-learning step with the determined punishment value
            _, predicted_next_role = q_learning_step(
                req.user_id, req.role, req.action, reward_value
            )
            
            # Update user's balances and cheat history
            users_col.update_one(
                {"user_id": req.user_id},
                {
                    "$inc": {f"balances.{token}": reward_value},
                    "$set": {"cheat_history": recent_cheats}
                }
            )
            
            # Recompute merit & role
            user_after = users_col.find_one({"user_id": req.user_id})
            merit_score = compute_user_merit_score(user_after)
            new_role = determine_role_from_merit(merit_score)
            users_col.update_one({"user_id": req.user_id}, {"$set": {"role": new_role}})
            
            # Log transaction
            try:
                log_transaction(req.user_id, req.action, reward_value, INTENT_MAP[req.action], "penalty", punishment_name)
            except Exception as e:
                logger.error(f"Failed to log transaction for cheat action: {str(e)}")
                # Continue with the response even if transaction logging fails
            
            # Create Rnanubandhan relationship if there's an affected user
            relationship = None
            if req.affected_user_id and req.affected_user_id != req.user_id:
                try:
                    relationship = rnanubandhan_manager.create_debt_relationship(
                        debtor_id=req.user_id,
                        receiver_id=req.affected_user_id,
                        action_type=req.action,
                        severity="medium",  # Cheat is generally considered medium severity
                        amount=abs(reward_value) * 0.5,  # Create debt proportional to punishment
                        description=req.relationship_description or f"Cheated, affecting user {req.affected_user_id}"
                    )
                except Exception as e:
                    # Log error but don't fail the main action
                    logger.warning(f"Failed to create Rnanubandhan relationship: {e}")
            
            response = {
                "user_id": req.user_id,
                "action": req.action,
                "current_role": new_role,
                "predicted_next_role": predicted_next_role,
                "merit_score": merit_score,
                "penalty_token": token,
                "penalty_value": reward_value,
                "penalty_level": cheat_level,
                "penalty_name": punishment_name,
                "cheats_in_period": len(recent_cheats),
                "action_flow": "action -> intent -> penalty_level -> punishment -> role_adjustment",
                "note": req.note
            }
            
            # Add relationship info if created
            if relationship:
                response["rnanubandhan_relationship"] = relationship
                
            return response
        
        # Handle non-cheat actions with standard reward system
        else:
            # Check if this action generates Paap
            paap_severity = classify_paap_action(req.action)
            
            # Q-learning step
            reward_value, predicted_next_role = q_learning_step(
                req.user_id, req.role, req.action, REWARD_MAP[req.action]["value"]
            )
        
            # Update token balances
            token = REWARD_MAP[req.action]["token"]
            users_col.update_one(
                {"user_id": req.user_id},
                {"$inc": {f"balances.{token}": reward_value}}
            )
            
            # Apply Paap tokens if applicable
            paap_applied = False
            paap_value = 0
            if paap_severity:
                user, severity, paap_value = apply_paap_tokens(user, req.action, 1.0)
                paap_applied = True
                
                # Update database
                users_col.update_one(
                    {"user_id": req.user_id},
                    {"$set": {"balances": user["balances"]}}
                )
                
                # Create an appeal stub if requested
                if req.note and "auto_appeal" in req.note.lower():
                    create_atonement_plan(req.user_id, req.action, paap_severity)
        
            # Recompute merit & role
            user_after = users_col.find_one({"user_id": req.user_id})
            merit_score = compute_user_merit_score(user_after)
            new_role = determine_role_from_merit(merit_score)
            users_col.update_one({"user_id": req.user_id}, {"$set": {"role": new_role}})
        
            # Log transaction
            reward_tier = "high" if token == "PunyaTokens" else "medium" if token == "SevaPoints" else "low"
            try:
                log_transaction(req.user_id, req.action, reward_value, INTENT_MAP[req.action], reward_tier)
            except Exception as e:
                logger.error(f"Failed to log transaction for action {req.action}: {str(e)}")
                # Continue with the response even if transaction logging fails
                
            # Create Rnanubandhan relationship if this is a harmful action affecting another user
            relationship = None
            if paap_applied and req.affected_user_id and req.affected_user_id != req.user_id:
                try:
                    relationship = rnanubandhan_manager.create_debt_relationship(
                        debtor_id=req.user_id,
                        receiver_id=req.affected_user_id,
                        action_type=req.action,
                        severity=paap_severity or "minor",  # Default to minor if severity is None
                        amount=paap_value * 0.3,  # Create debt proportional to Paap value
                        description=req.relationship_description or f"Action '{req.action}' affected user {req.affected_user_id}"
                    )
                except Exception as e:
                    # Log error but don't fail the main action
                    logger.warning(f"Failed to create Rnanubandhan relationship: {e}")
            
            response = {
                "user_id": req.user_id,
                "action": req.action,
                "current_role": new_role,
                "predicted_next_role": predicted_next_role,
                "merit_score": merit_score,
                "reward_token": token,
                "reward_tier": reward_tier,
                "action_flow": "action -> intent -> merit -> reward_tier -> redemption",
                "note": req.note
            }
            
            # Add Paap information if applicable
            if paap_applied:
                response["paap_generated"] = True
                response["paap_severity"] = paap_severity
                response["paap_value"] = paap_value
                response["appeal_created"] = "auto_appeal" in (req.note or "").lower()
                
            # Add relationship info if created
            if relationship:
                response["rnanubandhan_relationship"] = relationship
                
            return response
    except Exception as e:
        logger.error(f"Error processing log_action request for user {req.user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")