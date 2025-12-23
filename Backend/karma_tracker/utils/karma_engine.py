import numpy as np
from typing import Dict, List, Tuple, Any
from database import users_col
from config import TOKEN_ATTRIBUTES, ACTIONS, REWARD_MAP, KARMA_FACTORS, CORRECTIVE_GUIDANCE_WEIGHTS
from utils.karma_schema import calculate_weighted_karma_score, get_karma_weights
from utils.paap import classify_paap_action, calculate_paap_value
from utils.merit import determine_role_from_merit
from utils.karmic_predictor import analyze_dridha_adridha_influence, get_rnanubandhan_ledger

# Purushartha categories with their descriptions and modifiers
PURUSHARTHA = {
    "Dharma": {
        "description": "Righteousness, duty, and moral virtue",
        "modifier": KARMA_FACTORS["purushartha_modifiers"]["Dharma"],
        "positive_actions": ["completing_lessons", "helping_peers", "solving_doubts"],
        "negative_actions": ["cheat", "disrespect_guru", "break_promise", "false_speech"]
    },
    "Artha": {
        "description": "Wealth, prosperity, and economic values",
        "modifier": KARMA_FACTORS["purushartha_modifiers"]["Artha"],
        "positive_actions": ["selfless_service"],
        "negative_actions": ["theft", "violence"]
    },
    "Kama": {
        "description": "Desire, pleasure, and emotional fulfillment",
        "modifier": KARMA_FACTORS["purushartha_modifiers"]["Kama"],
        "positive_actions": ["helping_peers", "solving_doubts"],
        "negative_actions": ["harm_others", "violence"]
    },
    "Moksha": {
        "description": "Liberation, spiritual freedom, and enlightenment",
        "modifier": KARMA_FACTORS["purushartha_modifiers"]["Moksha"],
        "positive_actions": ["selfless_service", "completing_lessons"],
        "negative_actions": ["cheat", "disrespect_guru"]
    }
}

# Corrective guidance recommendations based on karma imbalances
CORRECTIVE_GUIDANCE = {
    "Seva": {
        "description": "Selfless service to others",
        "weight": CORRECTIVE_GUIDANCE_WEIGHTS["Seva"],
        "when_to_recommend": ["low_dharma", "high_paap"]
    },
    "Meditation": {
        "description": "Mindfulness and spiritual practice",
        "weight": CORRECTIVE_GUIDANCE_WEIGHTS["Meditation"],
        "when_to_recommend": ["high_stress", "kama_imbalance"]
    },
    "Daan": {
        "description": "Charitable giving and donations",
        "weight": CORRECTIVE_GUIDANCE_WEIGHTS["Daan"],
        "when_to_recommend": ["artha_imbalance", "low_dharma"]
    },
    "Tap": {
        "description": "Austerities and self-discipline practices",
        "weight": CORRECTIVE_GUIDANCE_WEIGHTS["Tap"],
        "when_to_recommend": ["high_paap", "kama_excess"]
    },
    "Bhakti": {
        "description": "Devotional practices and service",
        "weight": CORRECTIVE_GUIDANCE_WEIGHTS["Bhakti"],
        "when_to_recommend": ["spiritual_growth", "moksha_seek"]
    }
}

def evaluate_action_karma(user_doc: Dict, action: str, intensity: float = 1.0) -> Dict[str, Any]:
    """
    Evaluate the karmic impact of an action.
    
    Args:
        user_doc (dict): User document from database
        action (str): The action being evaluated
        intensity (float): Intensity of the action (0.0 to 2.0)
        
    Returns:
        dict: Detailed karmic evaluation including scores and recommendations
    """
    # Initialize result
    result = {
        "action": action,
        "intensity": intensity,
        "positive_impact": 0.0,
        "negative_impact": 0.0,
        "dridha_influence": 0.0,
        "adridha_influence": 0.0,
        "sanchita_change": 0.0,
        "prarabdha_change": 0.0,
        "rnanubandhan_change": 0.0,
        "purushartha_alignment": {},
        "net_karma": 0.0,
        "corrective_recommendations": []
    }
    
    # Check if action generates positive or negative karma
    is_paap = classify_paap_action(action)
    
    if is_paap:
        # Negative action (Paap)
        severity, paap_value = calculate_paap_value(action, intensity)
        result["negative_impact"] = paap_value
        
        # Apply to Rnanubandhan based on severity
        if severity:
            # Map Paap severity to Rnanubandhan severity
            rnanubandhan_severity = severity
            if severity == "maha":
                rnanubandhan_severity = "major"
            
            # Check if the severity exists in Rnanubandhan configuration
            if rnanubandhan_severity in TOKEN_ATTRIBUTES["Rnanubandhan"]:
                multiplier = TOKEN_ATTRIBUTES["Rnanubandhan"][rnanubandhan_severity]["multiplier"]
                result["rnanubandhan_change"] = paap_value * multiplier
            else:
                # Default multiplier if severity not found
                result["rnanubandhan_change"] = paap_value * 1.0
            
        # Apply to AdridhaKarma (volatile karma)
        result["adridha_influence"] = -paap_value * KARMA_FACTORS["negative_distribution"]["adridha"]
    else:
        # Positive action
        if action in REWARD_MAP:
            reward_info = REWARD_MAP[action]
            positive_value = reward_info["value"] * intensity
            result["positive_impact"] = positive_value
            
            result["sanchita_change"] = positive_value * KARMA_FACTORS["positive_distribution"]["sanchita"]
            
            # Apply to PrarabdhaKarma (current life karma)
            result["prarabdha_change"] = positive_value * KARMA_FACTORS["positive_distribution"]["prarabdha"]
            
            # Apply to DridhaKarma (stable karma) or AdridhaKarma based on action type
            if action in ["completing_lessons", "selfless_service"]:
                # More stable actions contribute to DridhaKarma
                result["dridha_influence"] = positive_value * KARMA_FACTORS["positive_distribution"]["dridha"]
            else:
                # Less stable actions contribute to AdridhaKarma
                result["adridha_influence"] = positive_value * KARMA_FACTORS["positive_distribution"]["adridha"]
        else:
            # Default positive action
            positive_value = 5.0 * intensity
            result["positive_impact"] = positive_value
            result["sanchita_change"] = positive_value * 0.3
            result["prarabdha_change"] = positive_value * 0.2
            result["dridha_influence"] = positive_value * 0.4
    
    # Calculate Purushartha alignment
    for purushartha, details in PURUSHARTHA.items():
        modifier = details["modifier"]
        if action in details["positive_actions"]:
            result["purushartha_alignment"][purushartha] = modifier
        elif action in details["negative_actions"]:
            result["purushartha_alignment"][purushartha] = -modifier
        else:
            result["purushartha_alignment"][purushartha] = 0.0
    
    # Calculate net karma
    result["net_karma"] = (result["positive_impact"] - result["negative_impact"]) * intensity
    
    # Generate corrective recommendations
    result["corrective_recommendations"] = _generate_corrective_guidance(result, user_doc)
    
    return result

def _generate_corrective_guidance(evaluation: Dict, user_doc: Dict) -> List[Dict]:
    """
    Generate corrective guidance based on karmic evaluation.
    
    Args:
        evaluation (dict): Action evaluation results
        user_doc (dict): User document from database
        
    Returns:
        list: List of corrective guidance recommendations
    """
    recommendations = []
    
    # Check for high negative impact
    if evaluation["negative_impact"] > 10:
        recommendations.append({
            "practice": "Tap",
            "reason": "High negative karma requires austerity to balance",
            "urgency": "high"
        })
    
    # Check for low positive impact
    if evaluation["positive_impact"] < 5:
        recommendations.append({
            "practice": "Seva",
            "reason": "Increase positive karma through selfless service",
            "urgency": "medium"
        })
    
    # Check for kama excess (based on negative actions in Kama domain)
    if "Kama" in evaluation["purushartha_alignment"] and evaluation["purushartha_alignment"]["Kama"] < 0:
        recommendations.append({
            "practice": "Meditation",
            "reason": "Balance desires through mindfulness practice",
            "urgency": "medium"
        })
    
    # Check for spiritual growth opportunities
    if evaluation["positive_impact"] > 15:
        recommendations.append({
            "practice": "Bhakti",
            "reason": "Channel positive energy into devotional practice",
            "urgency": "low"
        })
    
    # Add weight-based recommendations
    weighted_recommendations = []
    for rec in recommendations:
        practice = rec["practice"]
        if practice in CORRECTIVE_GUIDANCE:
            weight = CORRECTIVE_GUIDANCE[practice]["weight"]
            rec["weight"] = weight
            weighted_recommendations.append(rec)
    
    # Sort by weight (descending) and urgency
    urgency_order = {"high": 3, "medium": 2, "low": 1}
    weighted_recommendations.sort(
        key=lambda x: (x["weight"], urgency_order.get(x["urgency"], 0)), 
        reverse=True
    )
    
    return weighted_recommendations

def calculate_net_karma(user_doc: Dict) -> Dict[str, Any]:
    """
    Calculate the net karma for a user based on all karma types.
    
    Args:
        user_doc (dict): User document from database
        
    Returns:
        dict: Comprehensive karma calculation with breakdown
    """
    # Get weighted karma score
    weighted_score = calculate_weighted_karma_score(user_doc)
    
    # Get individual karma balances
    balances = user_doc.get("balances", {})
    
    # Calculate positive karma total
    positive_karma = 0
    for token in ["DharmaPoints", "SevaPoints", "PunyaTokens"]:
        positive_karma += balances.get(token, 0)
    
    # Calculate negative karma total
    negative_karma = 0
    if "PaapTokens" in balances:
        paap_tokens = balances["PaapTokens"]
        for severity in paap_tokens:
            if severity in TOKEN_ATTRIBUTES["PaapTokens"]:
                multiplier = TOKEN_ATTRIBUTES["PaapTokens"][severity]["multiplier"]
                negative_karma += paap_tokens[severity] * multiplier
    
    # Calculate new karma types
    dridha_karma = balances.get("DridhaKarma", 0)
    adridha_karma = balances.get("AdridhaKarma", 0)
    sanchita_karma = balances.get("SanchitaKarma", 0)
    prarabdha_karma = balances.get("PrarabdhaKarma", 0)
    
    # Calculate Rnanubandhan total
    rnanubandhan_total = 0.0
    if isinstance(balances, dict) and "Rnanubandhan" in balances:
        rnanubandhan = balances["Rnanubandhan"]
        # Support dict (severity levels), list-based entries, and legacy numeric values
        if isinstance(rnanubandhan, dict):
            for severity, amount in rnanubandhan.items():
                # Safely convert amount to float magnitude; skip non-numeric values
                try:
                    amount_val = abs(float(amount))
                except (TypeError, ValueError):
                    continue
                # Use configured multiplier if present; fallback to 'major'
                mult = TOKEN_ATTRIBUTES.get("Rnanubandhan", {}).get(severity, TOKEN_ATTRIBUTES["Rnanubandhan"]["major"]).get("multiplier", 1.0)
                rnanubandhan_total += amount_val * mult
        elif isinstance(rnanubandhan, list):
            for entry in rnanubandhan:
                if isinstance(entry, dict):
                    severity = entry.get("severity", "major")
                    amount = entry.get("amount", 0)
                    try:
                        amount_val = abs(float(amount))
                    except (TypeError, ValueError):
                        continue
                    mult = TOKEN_ATTRIBUTES.get("Rnanubandhan", {}).get(severity, TOKEN_ATTRIBUTES["Rnanubandhan"]["major"]).get("multiplier", 1.0)
                    rnanubandhan_total += amount_val * mult
                else:
                    # Interpret bare numeric values in list as legacy amounts
                    try:
                        amount_val = abs(float(entry))
                        mult = TOKEN_ATTRIBUTES["Rnanubandhan"]["major"]["multiplier"]
                        rnanubandhan_total += amount_val * mult
                    except (TypeError, ValueError):
                        continue
        else:
            # Legacy scalar value
            try:
                amount_val = abs(float(rnanubandhan))
                mult = TOKEN_ATTRIBUTES["Rnanubandhan"]["major"]["multiplier"]
                rnanubandhan_total = amount_val * mult
            except (TypeError, ValueError):
                rnanubandhan_total = 0.0

    # Calculate net karma
    net_karma = positive_karma - negative_karma + dridha_karma * KARMA_FACTORS["net_weights"]["dridha"] + adridha_karma * KARMA_FACTORS["net_weights"]["adridha"] + sanchita_karma + prarabdha_karma - rnanubandhan_total
    
    return {
        "net_karma": net_karma,
        "weighted_score": weighted_score,
        "breakdown": {
            "positive_karma": positive_karma,
            "negative_karma": negative_karma,
            "dridha_karma": dridha_karma,
            "adridha_karma": adridha_karma,
            "sanchita_karma": sanchita_karma,
            "prarabdha_karma": prarabdha_karma,
            "rnanubandhan": rnanubandhan_total
        }
    }

def determine_corrective_guidance(user_doc: Dict) -> List[Dict]:
    """
    Determine corrective guidance based on user's overall karma profile.
    Integrates with the new karmic predictor for advanced analysis.
    
    Args:
        user_doc (dict): User document from database
        
    Returns:
        list: List of corrective guidance recommendations
    """
    # Calculate net karma
    karma_calc = calculate_net_karma(user_doc)
    net_karma = karma_calc["net_karma"]
    
    # Get balances
    balances = user_doc.get("balances", {})
    
    # Initialize recommendations
    recommendations = []
    
    # Use karmic predictor for advanced analysis
    da_analysis = analyze_dridha_adridha_influence(user_doc)
    rnanubandhan_ledger = get_rnanubandhan_ledger(user_doc)
    
    # Check for overall negative karma
    if net_karma < 0:
        recommendations.append({
            "practice": "Seva",
            "reason": "Overall negative karma balance, focus on selfless service",
            "urgency": "high",
            "weight": CORRECTIVE_GUIDANCE["Seva"]["weight"]
        })
    
    # Check for high Paap
    total_paap = 0
    if "PaapTokens" in balances:
        paap_tokens = balances["PaapTokens"]
        for severity in paap_tokens:
            total_paap += paap_tokens[severity]
    
    if total_paap > 20:
        recommendations.append({
            "practice": "Tap",
            "reason": "High accumulation of negative actions, practice austerity",
            "urgency": "high",
            "weight": CORRECTIVE_GUIDANCE["Tap"]["weight"]
        })
    
    # Check for low DharmaPoints
    if balances.get("DharmaPoints", 0) < 10:
        recommendations.append({
            "practice": "Meditation",
            "reason": "Low dharmic foundation, strengthen through meditation",
            "urgency": "medium",
            "weight": CORRECTIVE_GUIDANCE["Meditation"]["weight"]
        })
    
    # Check for low SevaPoints
    if balances.get("SevaPoints", 0) < 15:
        recommendations.append({
            "practice": "Seva",
            "reason": "Insufficient service to others, increase seva activities",
            "urgency": "medium",
            "weight": CORRECTIVE_GUIDANCE["Seva"]["weight"]
        })
    
    # Check for spiritual growth potential
    punya_tokens = balances.get("PunyaTokens", 0)
    if punya_tokens > 50:
        recommendations.append({
            "practice": "Bhakti",
            "reason": "Strong positive karma foundation, channel into devotional practice",
            "urgency": "low",
            "weight": CORRECTIVE_GUIDANCE["Bhakti"]["weight"]
        })
    
    # Add recommendations based on Dridha/Adridha analysis
    if da_analysis["dridha_ratio"] < 0.3:
        # Very volatile karma patterns - need more stability
        recommendations.append({
            "practice": "Daily Practice",
            "reason": "Unstable karma patterns detected, establish daily spiritual practices",
            "urgency": "high",
            "weight": 1.6
        })
    elif da_analysis["dridha_ratio"] > 0.7:
        # Very stable karma patterns - corrective actions will be effective
        recommendations.append({
            "practice": "Advanced Practice",
            "reason": "Stable karma patterns detected, ready for advanced spiritual practices",
            "urgency": "medium",
            "weight": 1.5
        })
    
    # Add recommendations based on Rnanubandhan debt
    if rnanubandhan_ledger["total_debt"] > 30:
        recommendations.append({
            "practice": "Atonement",
            "reason": "Significant karmic debt detected, prioritize atonement practices",
            "urgency": "high",
            "weight": 1.7
        })
    
    # Sort recommendations by weight and urgency
    urgency_order = {"high": 3, "medium": 2, "low": 1}
    recommendations.sort(
        key=lambda x: (x["weight"], urgency_order.get(x["urgency"], 0)), 
        reverse=True
    )
    
    return recommendations

def integrate_with_q_learning(user_doc: Dict, action: str, reward: float) -> Tuple[float, str]:
    """
    Integrate karma adjustments with Q-learning scaffold.
    
    Args:
        user_doc (dict): User document from database
        action (str): The action taken
        reward (float): Base reward from Q-learning
        
    Returns:
        tuple: (adjusted_reward, next_role)
    """
    # Evaluate the karmic impact of the action
    karma_evaluation = evaluate_action_karma(user_doc, action)
    
    # Adjust reward based on karmic evaluation
    net_val = 0.0
    try:
        net_val = float(karma_evaluation.get("net_karma", 0.0))
    except (TypeError, ValueError):
        net_val = 0.0
    karmic_factor = (net_val / 100.0) if net_val != 0 else 0.0  # Normalize safely to avoid division-by-zero
    adjusted_reward = reward * (1 + karmic_factor)
    
    # Calculate new merit based on updated balances
    temp_balances = user_doc["balances"].copy()
    
    # Update balances based on karma evaluation
    # This is a simplified update - in a real implementation, you would update the actual database
    estimated_merit = (
        temp_balances.get("DharmaPoints", 0) * 1.0 + 
        temp_balances.get("SevaPoints", 0) * 1.2 + 
        temp_balances.get("PunyaTokens", 0) * 3.0
    )
    
    # Determine next role based on merit
    next_role = determine_role_from_merit(estimated_merit)
    
    return adjusted_reward, next_role

def get_purushartha_score(user_doc: Dict) -> Dict[str, float]:
    """
    Calculate the Purushartha alignment score for a user.
    
    Args:
        user_doc (dict): User document from database
        
    Returns:
        dict: Purushartha scores for each category
    """
    balances = user_doc.get("balances", {})
    
    # Initialize scores
    scores = {p: 0.0 for p in PURUSHARTHA.keys()}
    
    # Calculate scores based on token balances and Purushartha modifiers
    dharma_points = balances.get("DharmaPoints", 0)
    seva_points = balances.get("SevaPoints", 0)
    punya_tokens = balances.get("PunyaTokens", 0)
    
    # Dharma score (righteousness, duty)
    scores["Dharma"] = dharma_points * 1.0 + seva_points * 0.5
    
    # Artha score (wealth, prosperity)
    scores["Artha"] = seva_points * 0.3 + punya_tokens * 0.2
    
    # Kama score (desire, pleasure)
    scores["Kama"] = seva_points * 0.4 + dharma_points * 0.2
    
    # Moksha score (liberation, spiritual freedom)
    scores["Moksha"] = dharma_points * 1.2 + punya_tokens * 0.8
    
    # Apply modifiers
    for purushartha in scores:
        scores[purushartha] *= PURUSHARTHA[purushartha]["modifier"]
    
    return scores