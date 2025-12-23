from config import LOKA_THRESHOLDS
from utils.merit import compute_user_merit_score

def calculate_net_karma(user):
    """
    Calculate the net karma score by weighing Punya against Paap.
    
    Args:
        user (dict): User document from the database
        
    Returns:
        float: Net karma score
    """
    # Calculate positive karma (Punya)
    punya_score = 0
    if "balances" in user:
        balances = user["balances"]
        # Sum up positive tokens with their weights
        if "DharmaPoints" in balances:
            punya_score += balances["DharmaPoints"] * 1.0
        if "SevaPoints" in balances:
            punya_score += balances["SevaPoints"] * 1.2
        if "PunyaTokens" in balances:
            punya_score += balances["PunyaTokens"] * 3.0
    
    # Calculate negative karma (Paap)
    paap_score = 0
    if "balances" in user and "PaapTokens" in user["balances"]:
        paap_tokens = user["balances"]["PaapTokens"]
        # Ensure PaapTokens is a dictionary with severity categories
        if isinstance(paap_tokens, dict):
            # Sum up negative tokens with their weights
            if "minor" in paap_tokens:
                paap_score += paap_tokens["minor"] * 1.0
            if "medium" in paap_tokens:
                paap_score += paap_tokens["medium"] * 2.5
            if "maha" in paap_tokens:
                paap_score += paap_tokens["maha"] * 5.0
        else:
            # If PaapTokens is not a dict, treat it as 0
            paap_score = 0
    
    # Net karma is punya minus paap
    return punya_score - paap_score

def compute_loka_assignment(user):
    """
    Compute the loka assignment based on the user's net karma.
    
    Args:
        user (dict): User document from the database
        
    Returns:
        tuple: (loka_name, description)
    """
    net_karma = calculate_net_karma(user)
    
    # Determine loka based on thresholds
    assigned_loka = "Mrityuloka"  # Default loka (middle realm)
    description = "The mortal realm, where souls continue their journey."
    
    for loka, threshold in LOKA_THRESHOLDS.items():
        if net_karma >= threshold["min_karma"] and net_karma <= threshold["max_karma"]:
            assigned_loka = loka
            description = threshold["description"]
            break
    
    return assigned_loka, description

def create_rebirth_carryover(user):
    """
    Create a rebirth carryover object for a user.
    
    Args:
        user (dict): User document from the database
        
    Returns:
        dict: Rebirth carryover object
    """
    # Calculate carryover values
    net_karma = calculate_net_karma(user)
    
    # Determine how much karma carries over to next life
    # Positive karma carries over at 10%
    carryover_punya = 0
    if net_karma > 0:
        carryover_punya = net_karma * 0.1
    
    # Negative karma carries over at 30% (karmic debt is harder to escape)
    carryover_paap = 0
    if net_karma < 0:
        carryover_paap = abs(net_karma) * 0.3
    
    # Determine starting level based on net karma
    starting_level = "learner"  # Default starting level
    if net_karma > 100:
        starting_level = "volunteer"
    
    # Create the carryover object
    carryover = {
        "carryover_paap": carryover_paap,
        "carryover_punya": carryover_punya,
        "starting_level": starting_level
    }
    
    return carryover

def apply_rebirth(user_id, carryover):
    """
    Apply rebirth effects to a user, resetting their state but applying carryover.
    
    Args:
        user_id (str): The user's ID
        carryover (dict): Rebirth carryover object
        
    Returns:
        dict: Updated user document
    """
    from database import users_col
    
    # Get the user
    user = users_col.find_one({"user_id": user_id})
    if not user:
        return None
    
    # Reset user state but apply carryover
    new_balances = {
        "DharmaPoints": 0,
        "SevaPoints": 0,
        "PunyaTokens": 0,
        "PaapTokens": {
            "minor": 0,
            "medium": 0,
            "maha": 0
        }
    }
    
    # Apply carryover punya
    if carryover["carryover_punya"] > 0:
        new_balances["PunyaTokens"] = carryover["carryover_punya"]
    
    # Apply carryover paap
    if carryover["carryover_paap"] > 0:
        # Distribute paap across categories
        paap_per_category = carryover["carryover_paap"] / 3
        new_balances["PaapTokens"]["minor"] = paap_per_category
        new_balances["PaapTokens"]["medium"] = paap_per_category
        new_balances["PaapTokens"]["maha"] = paap_per_category
    
    # Update user with new state
    users_col.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "balances": new_balances,
                "role": carryover["starting_level"],
                "rebirth_count": user.get("rebirth_count", 0) + 1,
                "last_rebirth": {"timestamp": datetime.now(timezone.utc), "carryover": carryover}
            },
            "$unset": {"atonement_plans": ""}  # Clear atonement plans
        }
    )
    
    # Return updated user
    return users_col.find_one({"user_id": user_id})