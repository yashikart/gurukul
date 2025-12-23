import json
from datetime import datetime
from database import users_col
from config import TOKEN_ATTRIBUTES

def now_utc():
    return datetime.utcnow()

def apply_dridha_adridha_karma(user_doc, karma_type, value):
    """
    Apply DridhaKarma or AdridhaKarma to a user's balance.
    
    Args:
        user_doc (dict): User document from database
        karma_type (str): Either 'DridhaKarma' or 'AdridhaKarma'
        value (float): The karma value to add
        
    Returns:
        dict: Updated user document
    """
    if karma_type not in ['DridhaKarma', 'AdridhaKarma']:
        raise ValueError("karma_type must be either 'DridhaKarma' or 'AdridhaKarma'")
        
    # Initialize karma type if not present
    if karma_type not in user_doc["balances"]:
        user_doc["balances"][karma_type] = 0
        
    # Add karma value
    user_doc["balances"][karma_type] += value
    
    return user_doc

def apply_sanchita_karma(user_doc, value):
    """
    Apply SanchitaKarma to a user's balance.
    
    Args:
        user_doc (dict): User document from database
        value (float): The karma value to add
        
    Returns:
        dict: Updated user document
    """
    # Initialize SanchitaKarma if not present
    if "SanchitaKarma" not in user_doc["balances"]:
        user_doc["balances"]["SanchitaKarma"] = 0
        
    # Add karma value
    user_doc["balances"]["SanchitaKarma"] += value
    
    return user_doc

def apply_prarabdha_karma(user_doc, value):
    """
    Apply PrarabdhaKarma to a user's balance.
    
    Args:
        user_doc (dict): User document from database
        value (float): The karma value to add
        
    Returns:
        dict: Updated user document
    """
    # Initialize PrarabdhaKarma if not present
    if "PrarabdhaKarma" not in user_doc["balances"]:
        user_doc["balances"]["PrarabdhaKarma"] = 0
        
    # Add karma value
    user_doc["balances"]["PrarabdhaKarma"] += value
    
    return user_doc

def apply_rnanubandhan(user_doc, severity, value):
    """
    Apply Rnanubandhan to a user's balance based on severity.
    
    Args:
        user_doc (dict): User document from database
        severity (str): The severity class ('minor', 'medium', 'major')
        value (float): The karma value to add
        
    Returns:
        tuple: (updated_user_doc, actual_value)
    """
    if severity not in ['minor', 'medium', 'major']:
        raise ValueError("severity must be either 'minor', 'medium', or 'major'")
        
    # Initialize Rnanubandhan if not present or convert from legacy structure
    if "Rnanubandhan" not in user_doc["balances"]:
        user_doc["balances"]["Rnanubandhan"] = {}
    elif not isinstance(user_doc["balances"]["Rnanubandhan"], dict):
        # Convert legacy numeric structure to dictionary
        user_doc["balances"]["Rnanubandhan"] = {"minor": 0.0, "medium": 0.0, "major": 0.0}
        
    # Initialize severity class if not present
    if severity not in user_doc["balances"]["Rnanubandhan"]:
        user_doc["balances"]["Rnanubandhan"][severity] = 0
        
    # Add karma value to the appropriate severity class
    user_doc["balances"]["Rnanubandhan"][severity] += value
    
    # Calculate actual value with multiplier
    multiplier = TOKEN_ATTRIBUTES["Rnanubandhan"][severity]["multiplier"]
    actual_value = value * multiplier
    
    return user_doc, actual_value

def get_karma_weights():
    """
    Get the weights for different karma types that can influence future calculations.
    
    Returns:
        dict: Weights for each karma type
    """
    weights = {}
    for karma_type in ['DridhaKarma', 'AdridhaKarma', 'SanchitaKarma', 'PrarabdhaKarma']:
        if karma_type in TOKEN_ATTRIBUTES:
            weights[karma_type] = TOKEN_ATTRIBUTES[karma_type].get('weight', 1.0)
    
    # For Rnanubandhan, we'll return the weights for each severity class
    if 'Rnanubandhan' in TOKEN_ATTRIBUTES:
        weights['Rnanubandhan'] = {}
        for severity in TOKEN_ATTRIBUTES['Rnanubandhan']:
            if severity not in ['minor', 'medium', 'major']:
                continue
            weights['Rnanubandhan'][severity] = TOKEN_ATTRIBUTES['Rnanubandhan'][severity].get('multiplier', 1.0)
            
    return weights

def calculate_weighted_karma_score(user_doc):
    """
    Calculate the total weighted karma score for a user.
    
    Args:
        user_doc (dict): User document from database
        
    Returns:
        float: Total weighted karma score
    """
    weights = get_karma_weights()
    total_score = 0.0
    
    # Calculate score for DridhaKarma and AdridhaKarma
    for karma_type in ['DridhaKarma', 'AdridhaKarma']:
        if karma_type in user_doc["balances"]:
            weight = weights.get(karma_type, 1.0)
            total_score += user_doc["balances"][karma_type] * weight
    
    # Calculate score for SanchitaKarma and PrarabdhaKarma
    for karma_type in ['SanchitaKarma', 'PrarabdhaKarma']:
        if karma_type in user_doc["balances"]:
            weight = weights.get(karma_type, 1.0)
            total_score += user_doc["balances"][karma_type] * weight
            
    # Calculate score for Rnanubandhan
    if "Rnanubandhan" in user_doc["balances"]:
        rnanubandhan = user_doc["balances"]["Rnanubandhan"]
        # Dict structure with severity levels
        if isinstance(rnanubandhan, dict):
            for severity, amount in rnanubandhan.items():
                try:
                    amount_val = float(amount)
                except (TypeError, ValueError):
                    continue
                multiplier = weights.get('Rnanubandhan', {}).get(severity, 1.0)
                total_score += amount_val * multiplier
        # List structure supporting dict and numeric entries
        elif isinstance(rnanubandhan, list):
            for entry in rnanubandhan:
                if isinstance(entry, dict):
                    severity = entry.get("severity", "major")
                    amount = entry.get("amount", 0)
                    try:
                        amount_val = float(amount)
                    except (TypeError, ValueError):
                        continue
                    multiplier = weights.get('Rnanubandhan', {}).get(severity, weights.get('Rnanubandhan', {}).get('major', 1.0))
                    total_score += amount_val * multiplier
                else:
                    try:
                        amount_val = float(entry)
                        multiplier = weights.get('Rnanubandhan', {}).get('major', 1.0)
                        total_score += amount_val * multiplier
                    except (TypeError, ValueError):
                        continue
        else:
            # Legacy scalar value
            try:
                amount_val = float(rnanubandhan)
                multiplier = weights.get('Rnanubandhan', {}).get('major', 4.0)
                total_score += amount_val * multiplier
            except (TypeError, ValueError):
                pass
            
    return total_score