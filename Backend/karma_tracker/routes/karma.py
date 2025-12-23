from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid
from database import users_col, transactions_col, karma_events_col
from utils.tokens import apply_decay_and_expiry
from utils.merit import compute_user_merit_score, determine_role_from_merit
from utils.paap import get_total_paap_score, apply_paap_tokens, classify_paap_action
from utils.loka import calculate_net_karma
from utils.atonement import validate_atonement_proof
from utils.karma_schema import calculate_weighted_karma_score
from utils.karma_engine import evaluate_action_karma, determine_corrective_guidance
from utils.qlearning import q_learning_step, atonement_q_learning_step
from utils.utils_user import create_user_if_missing
from validation_middleware import validation_dependency, validation_middleware
from config import TOKEN_ATTRIBUTES, ACTIONS, REWARD_MAP, INTENT_MAP, ATONEMENT_REWARDS
import logging


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class KarmaProfileResponse(BaseModel):
    user_id: str
    role: str
    merit_score: float
    paap_score: float
    net_karma: float
    weighted_karma_score: float
    balances: Dict[str, Any]
    action_stats: Dict[str, int]
    corrective_guidance: List[Dict[str, Any]]
    module_scores: Dict[str, float]
    last_updated: datetime

class LogActionRequest(BaseModel):
    user_id: str
    action: str
    role: Optional[str] = "learner"
    intensity: Optional[float] = 1.0
    context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class LogActionResponse(BaseModel):
    user_id: str
    action: str
    current_role: str
    predicted_next_role: str
    merit_score: float
    karma_impact: float
    reward_token: Optional[str] = None
    reward_value: Optional[float] = None
    paap_generated: Optional[bool] = False
    paap_severity: Optional[str] = None
    paap_value: Optional[float] = None
    corrective_recommendations: List[Dict[str, Any]]
    module_impacts: Dict[str, float]
    transaction_id: str

class AtonementSubmissionRequest(BaseModel):
    user_id: str
    plan_id: str
    atonement_type: str
    amount: float
    proof_text: Optional[str] = None
    tx_hash: Optional[str] = None

class AtonementSubmissionResponse(BaseModel):
    status: str
    message: str
    user_id: str
    plan_id: str
    karma_adjustment: float
    paap_reduction: float
    new_role: str
    module_impacts: Dict[str, float]
    transaction_id: str

@router.get("/karma/{user_id}", response_model=KarmaProfileResponse)
async def get_karma_profile(user_id: str, _: bool = Depends(validation_dependency)):
    """
    Get full karma profile for a user.
    
    Args:
        user_id (str): The ID of the user
        
    Returns:
        KarmaProfileResponse: Complete karma profile including balances, scores, and guidance
    """
    event_id = None
    try:
        # Log the request
        event_id = str(uuid.uuid4())
        karma_events_col.insert_one({
            "event_id": event_id,
            "event_type": "karma_profile_request",
            "data": {"user_id": user_id},
            "timestamp": datetime.utcnow(),
            "source": "karma_api",
            "status": "processing"
        })
        
        # Get user data
        user = users_col.find_one({"user_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Apply decay and expiry
        user = apply_decay_and_expiry(user)
        
        # Calculate various karma scores
        merit_score = compute_user_merit_score(user)
        paap_score = get_total_paap_score(user)
        net_karma = calculate_net_karma(user)  # This returns a float
        weighted_karma_score = calculate_weighted_karma_score(user)
        
        # Get action statistics via single aggregation
        stats = list(transactions_col.aggregate([
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": None,
                "total_actions": {"$sum": 1},
                "completed_atonements": {"$sum": {"$cond": [{"$eq": ["$action", "atonement_completed"]}, 1, 0]}}
            }}
        ]))
        if stats:
            total_actions = stats[0].get("total_actions", 0)
            completed_atonements = stats[0].get("completed_atonements", 0)
        else:
            total_actions = 0
            completed_atonements = 0
        pending_atonements = 0
        
        # Get corrective guidance
        corrective_guidance = determine_corrective_guidance(user)
        
        # Calculate module scores (for Finance, InsightFlow, Gurukul, and Game)
        module_scores = {
            "finance": _calculate_finance_score(user),
            "insightflow": _calculate_insightflow_score(user),
            "gurukul": _calculate_gurukul_score(user),
            "game": _calculate_game_score(user)
        }
        
        # Update event status
        karma_events_col.update_one(
            {"event_id": event_id},
            {
                "$set": {
                    "status": "completed",
                    "response_data": {
                        "user_id": user_id,
                        "role": user.get("role"),
                        "merit_score": merit_score,
                        "paap_score": paap_score,
                        "net_karma": net_karma,  # This is a float
                        "weighted_karma_score": weighted_karma_score
                    },
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return KarmaProfileResponse(
            user_id=user_id,
            role=user.get("role", "learner"),
            merit_score=merit_score,
            paap_score=paap_score,
            net_karma=net_karma,  # This is a float
            weighted_karma_score=weighted_karma_score,
            balances=user.get("balances", {}),
            action_stats={
                "total_actions": total_actions,
                "pending_atonements": pending_atonements,
                "completed_atonements": completed_atonements
            },
            corrective_guidance=corrective_guidance,
            module_scores=module_scores,
            last_updated=datetime.utcnow()
        )
        
    except HTTPException as e:
        # Log error
        if event_id:
            karma_events_col.update_one(
                {"event_id": event_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": e.detail if hasattr(e, 'detail') else str(e),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        logger.warning(f"Request error getting karma profile for user {user_id}: {e.detail if hasattr(e, 'detail') else str(e)}")
        raise e
    except Exception as e:
        msg = f"Database error: {str(e)}" if 'pymongo' in type(e).__module__ else f"Internal server error: {str(e)}"
        if event_id:
            karma_events_col.update_one(
                {"event_id": event_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": msg,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        logger.error(f"{'Database error' if 'pymongo' in type(e).__module__ else 'Error'} getting karma profile for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=msg)

@router.post("/log-action/", response_model=LogActionResponse)
async def log_action(req: LogActionRequest, _: bool = Depends(validation_dependency)):
    """
    Log user action and update karma.
    
    Args:
        req (LogActionRequest): Action details
        
    Returns:
        LogActionResponse: Action processing results
    """
    event_id = None
    try:
        # Log the request
        event_id = str(uuid.uuid4())
        karma_events_col.insert_one({
            "event_id": event_id,
            "event_type": "log_action_request",
            "data": req.dict(),
            "timestamp": datetime.utcnow(),
            "source": "karma_api",
            "status": "processing"
        })
        
        # Ensure user exists
        user = users_col.find_one({"user_id": req.user_id})
        if not user:
            user = create_user_if_missing(req.user_id, req.role or "learner")
        
        # Apply decay/expiry
        user = apply_decay_and_expiry(user)
        
        # Evaluate karmic impact using the karma engine
        karma_evaluation = evaluate_action_karma(user, req.action, req.intensity or 1.0)
        
        # Get Q-learning reward
        reward_value = 0
        predicted_next_role = user.get("role", "learner")
        
        if req.action in REWARD_MAP:
            reward_info = REWARD_MAP[req.action]
            base_reward = reward_info["value"] * (req.intensity or 1.0)
            
            # Apply Q-learning step
            reward_value, predicted_next_role = q_learning_step(
                req.user_id, user.get("role", "learner"), req.action, base_reward
            )
        
        # Update token balances based on karma evaluation
        token = None
        if req.action in REWARD_MAP:
            token = REWARD_MAP[req.action]["token"]
            
            # Apply the reward
            users_col.update_one(
                {"user_id": req.user_id},
                {"$inc": {f"balances.{token}": reward_value}}
            )
            
            # Update local user balances to avoid an extra read
            user.setdefault("balances", {})
            user["balances"][token] = user["balances"].get(token, 0) + reward_value
        
        # Handle Paap generation if applicable
        paap_generated = False
        paap_severity = None
        paap_value = 0
        if karma_evaluation["negative_impact"] > 0:
            paap_severity = classify_paap_action(req.action)
            if paap_severity:
                # Apply Paap tokens
                user, severity, paap_value = apply_paap_tokens(user, req.action, karma_evaluation["negative_impact"])
                paap_generated = True
                
                # Update database
                users_col.update_one(
                    {"user_id": req.user_id},
                    {"$set": {"balances": user["balances"]}}
                )
        
        # Update Sanchita/Prarabdha/Rnanubandhan if applicable
        _update_advanced_karma_types(req.user_id, karma_evaluation)
        
        # Recompute merit & role
        user_after = user
        merit_score = compute_user_merit_score(user_after)
        new_role = determine_role_from_merit(merit_score)
        users_col.update_one({"user_id": req.user_id}, {"$set": {"role": new_role}})
        
        # Log transaction
        transaction_id = str(uuid.uuid4())
        intent = INTENT_MAP.get(req.action, "unknown")
        tier = "high" if token == "PunyaTokens" else "medium" if token == "SevaPoints" else "low"
        
        transactions_col.insert_one({
            "transaction_id": transaction_id,
            "user_id": req.user_id,
            "action": req.action,
            "value": reward_value,
            "intent": intent,
            "tier": tier,
            "timestamp": datetime.utcnow(),
            "context": req.context,
            "metadata": req.metadata
        })
        
        # Generate corrective recommendations
        corrective_recommendations = karma_evaluation["corrective_recommendations"]
        
        # Calculate module impacts
        module_impacts = {
            "finance": _calculate_finance_impact(karma_evaluation),
            "insightflow": _calculate_insightflow_impact(karma_evaluation),
            "gurukul": _calculate_gurukul_impact(karma_evaluation),
            "game": _calculate_game_impact(karma_evaluation)
        }
        
        # Update event status
        karma_events_col.update_one(
            {"event_id": event_id},
            {
                "$set": {
                    "status": "completed",
                    "response_data": {
                        "user_id": req.user_id,
                        "action": req.action,
                        "current_role": new_role,
                        "predicted_next_role": predicted_next_role,
                        "merit_score": merit_score,
                        "karma_impact": karma_evaluation["net_karma"]
                    },
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return LogActionResponse(
            user_id=req.user_id,
            action=req.action,
            current_role=new_role,
            predicted_next_role=predicted_next_role,
            merit_score=merit_score,
            karma_impact=karma_evaluation["net_karma"],
            reward_token=token,
            reward_value=reward_value,
            paap_generated=paap_generated,
            paap_severity=paap_severity,
            paap_value=paap_value,
            corrective_recommendations=corrective_recommendations,
            module_impacts=module_impacts,
            transaction_id=transaction_id
        )
        
    except HTTPException as e:
        # Log error
        if event_id:
            karma_events_col.update_one(
                {"event_id": event_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": e.detail if hasattr(e, 'detail') else str(e),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        logger.warning(f"Request error logging action for user {req.user_id}: {e.detail if hasattr(e, 'detail') else str(e)}")
        raise e
    except Exception as e:
        msg = f"Database error: {str(e)}" if 'pymongo' in type(e).__module__ else f"Internal server error: {str(e)}"
        if event_id:
            karma_events_col.update_one(
                {"event_id": event_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": msg,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        logger.error(f"{'Database error' if 'pymongo' in type(e).__module__ else 'Error'} logging action for user {req.user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=msg)

@router.post("/submit-atonement/", response_model=AtonementSubmissionResponse)
async def submit_atonement(req: AtonementSubmissionRequest, _: bool = Depends(validation_dependency)):
    """
    Validate atonement completion and reduce PaapTokens.
    
    Args:
        req (AtonementSubmissionRequest): Atonement details
        
    Returns:
        AtonementSubmissionResponse: Atonement processing results
    """
    event_id = None
    try:
        # Log the request
        event_id = str(uuid.uuid4())
        karma_events_col.insert_one({
            "event_id": event_id,
            "event_type": "atonement_submission_request",
            "data": req.dict(),
            "timestamp": datetime.utcnow(),
            "source": "karma_api",
            "status": "processing"
        })
        
        # Validate the atonement submission
        success, message, updated_plan = validate_atonement_proof(
            req.plan_id,
            req.atonement_type,
            req.amount,
            req.proof_text,
            req.tx_hash
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        # Get user data
        user = users_col.find_one({"user_id": req.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Apply decay/expiry
        user = apply_decay_and_expiry(user)
        
        # Get the severity class from the atonement plan
        severity_class = "minor"
        if isinstance(updated_plan, dict):
            sc = updated_plan.get("severity_class")
            if isinstance(sc, str):
                severity_class = sc
        
        # Apply Q-learning update for atonement completion
        reward_value, next_role = atonement_q_learning_step(req.user_id, severity_class)
        
        # Calculate Paap reduction based on atonement
        paap_reduction = 0
        if severity_class in ATONEMENT_REWARDS:
            reward_info = ATONEMENT_REWARDS[severity_class]
            paap_reduction = abs(reward_info["value"])
            
            # Update user's PaapTokens balance
            token = reward_info["token"]
            if token.startswith("PaapTokens."):
                paap_severity = token.split(".")[1]
                users_col.update_one(
                    {"user_id": req.user_id},
                    {"$inc": {f"balances.PaapTokens.{paap_severity}": -paap_reduction}}
                )
        
        # Recalculate user's role
        user_after = users_col.find_one({"user_id": req.user_id})
        merit_score = compute_user_merit_score(user_after)
        new_role = determine_role_from_merit(merit_score)
        users_col.update_one({"user_id": req.user_id}, {"$set": {"role": new_role}})
        
        # Log transaction
        transaction_id = str(uuid.uuid4())
        transactions_col.insert_one({
            "transaction_id": transaction_id,
            "user_id": req.user_id,
            "action": "atonement_completed",
            "value": reward_value,
            "intent": "atonement",
            "tier": "atonement",
            "timestamp": datetime.utcnow(),
            "context": f"Atonement type: {req.atonement_type}",
            "metadata": {
                "plan_id": req.plan_id,
                "atonement_type": req.atonement_type,
                "amount": req.amount
            }
        })
        
        # Calculate karma adjustment
        karma_adjustment = reward_value  # Positive reward for completing atonement
        
        # Calculate module impacts
        module_impacts = {
            "finance": _calculate_finance_atonement_impact(severity_class),
            "insightflow": _calculate_insightflow_atonement_impact(severity_class),
            "gurukul": _calculate_gurukul_atonement_impact(severity_class),
            "game": _calculate_game_atonement_impact(severity_class)
        }
        
        # Update event status
        karma_events_col.update_one(
            {"event_id": event_id},
            {
                "$set": {
                    "status": "completed",
                    "response_data": {
                        "user_id": req.user_id,
                        "plan_id": req.plan_id,
                        "karma_adjustment": karma_adjustment,
                        "paap_reduction": paap_reduction,
                        "new_role": new_role
                    },
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return AtonementSubmissionResponse(
            status="success",
            message=message,
            user_id=req.user_id,
            plan_id=req.plan_id,
            karma_adjustment=karma_adjustment,
            paap_reduction=paap_reduction,
            new_role=new_role,
            module_impacts=module_impacts,
            transaction_id=transaction_id
        )
        
    except HTTPException as e:
        # Log error
        if event_id:
            karma_events_col.update_one(
                {"event_id": event_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": e.detail if hasattr(e, 'detail') else str(e),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        logger.warning(f"Request error submitting atonement for user {req.user_id}: {e.detail if hasattr(e, 'detail') else str(e)}")
        raise e
    except Exception as e:
        msg = f"Database error: {str(e)}" if 'pymongo' in type(e).__module__ else f"Internal server error: {str(e)}"
        if event_id:
            karma_events_col.update_one(
                {"event_id": event_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": msg,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        logger.error(f"{'Database error' if 'pymongo' in type(e).__module__ else 'Error'} submitting atonement for user {req.user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=msg)

def _update_advanced_karma_types(user_id: str, karma_evaluation: Dict[str, Any]):
    """
    Update advanced karma types (Sanchita, Prarabdha, Rnanubandhan) based on evaluation.
    """
    # This is a simplified implementation - in a real system, you would have more complex logic
    updates = {}
    
    if karma_evaluation["sanchita_change"] != 0:
        updates["balances.SanchitaKarma"] = karma_evaluation["sanchita_change"]
        
    if karma_evaluation["prarabdha_change"] != 0:
        updates["balances.PrarabdhaKarma"] = karma_evaluation["prarabdha_change"]
        
    if karma_evaluation["rnanubandhan_change"] != 0:
        # This is simplified - you would need to determine the severity class
        updates["balances.Rnanubandhan.minor"] = karma_evaluation["rnanubandhan_change"]
    
    if updates:
        users_col.update_one(
            {"user_id": user_id},
            {"$inc": updates}
        )

# Module score calculation functions
def _calculate_finance_score(user: Dict) -> float:
    """Calculate finance module score based on user's karma."""
    # Finance score based on PunyaTokens and SevaPoints (representing ethical wealth generation)
    punya = user.get("balances", {}).get("PunyaTokens", 0)
    seva = user.get("balances", {}).get("SevaPoints", 0)
    return (punya * 2.0) + (seva * 1.5)

def _calculate_insightflow_score(user: Dict) -> float:
    """Calculate InsightFlow module score based on user's karma."""
    # InsightFlow score based on DharmaPoints and learning actions
    dharma = user.get("balances", {}).get("DharmaPoints", 0)
    return dharma * 2.5

def _calculate_gurukul_score(user: Dict) -> float:
    """Calculate Gurukul module score based on user's karma."""
    # Gurukul score based on teaching/helping others
    seva = user.get("balances", {}).get("SevaPoints", 0)
    dharma = user.get("balances", {}).get("DharmaPoints", 0)
    return (seva * 2.0) + (dharma * 1.5)

def _calculate_game_score(user: Dict) -> float:
    """Calculate Game module score based on user's karma."""
    # Game score based on overall engagement and positive actions
    dharma = user.get("balances", {}).get("DharmaPoints", 0)
    seva = user.get("balances", {}).get("SevaPoints", 0)
    punya = user.get("balances", {}).get("PunyaTokens", 0)
    return (dharma * 1.0) + (seva * 1.2) + (punya * 1.5)

# Module impact calculation functions
def _calculate_finance_impact(karma_evaluation: Dict) -> float:
    """Calculate finance impact of an action."""
    # Positive impact on finance from SevaPoints and PunyaTokens
    positive = karma_evaluation["positive_impact"]
    return positive * 0.8 if positive > 0 else 0

def _calculate_insightflow_impact(karma_evaluation: Dict) -> float:
    """Calculate InsightFlow impact of an action."""
    # Impact on learning/growth from DharmaPoints
    return karma_evaluation["dridha_influence"] * 1.2

def _calculate_gurukul_impact(karma_evaluation: Dict) -> float:
    """Calculate Gurukul impact of an action."""
    # Impact on teaching/helping from SevaPoints
    return karma_evaluation["positive_impact"] * 0.9

def _calculate_game_impact(karma_evaluation: Dict) -> float:
    """Calculate Game impact of an action."""
    # Overall engagement impact
    return karma_evaluation["net_karma"] * 0.7

def _calculate_finance_atonement_impact(severity_class: str) -> float:
    """Calculate finance impact of atonement completion."""
    impact_map = {"minor": 1.0, "medium": 2.0, "maha": 3.0}
    return impact_map.get(severity_class, 1.0) * 2.0

def _calculate_insightflow_atonement_impact(severity_class: str) -> float:
    """Calculate InsightFlow impact of atonement completion."""
    impact_map = {"minor": 1.0, "medium": 2.0, "maha": 3.0}
    return impact_map.get(severity_class, 1.0) * 1.5

def _calculate_gurukul_atonement_impact(severity_class: str) -> float:
    """Calculate Gurukul impact of atonement completion."""
    impact_map = {"minor": 1.0, "medium": 2.0, "maha": 3.0}
    return impact_map.get(severity_class, 1.0) * 1.8

def _calculate_game_atonement_impact(severity_class: str) -> float:
    """Calculate Game impact of atonement completion."""
    impact_map = {"minor": 1.0, "medium": 2.0, "maha": 3.0}
    return impact_map.get(severity_class, 1.0) * 1.2