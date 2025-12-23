from config import PAAP_CLASSES, TOKEN_ATTRIBUTES

def classify_paap_action(action):
    """
    Classify an action into a Paap severity category.
    
    Args:
        action (str): The action to classify
        
    Returns:
        str: The severity class ('minor', 'medium', 'maha') or None if not a Paap action
    """
    return PAAP_CLASSES.get(action)

def calculate_paap_value(action, base_value=1.0):
    """
    Calculate the Paap value for an action based on its severity class.
    
    Args:
        action (str): The action to calculate Paap for
        base_value (float): Base value for the Paap calculation
        
    Returns:
        tuple: (severity_class, paap_value) or (None, 0) if not a Paap action
    """
    severity_class = classify_paap_action(action)
    if not severity_class:
        return None, 0
        
    multiplier = TOKEN_ATTRIBUTES["PaapTokens"][severity_class]["multiplier"]
    return severity_class, base_value * multiplier

def apply_paap_tokens(user_doc, action, base_value=1.0):
    """
    Apply PaapTokens to a user's balance based on an action.
    
    Args:
        user_doc (dict): User document from database
        action (str): The action that generated Paap
        base_value (float): Base value for the Paap calculation
        
    Returns:
        tuple: (updated_user_doc, severity_class, paap_value)
    """
    severity_class, paap_value = calculate_paap_value(action, base_value)
    
    if not severity_class or paap_value == 0:
        return user_doc, None, 0
        
    # Initialize PaapTokens if not present
    if "PaapTokens" not in user_doc["balances"]:
        user_doc["balances"]["PaapTokens"] = {}
        
    # Initialize severity class if not present
    if severity_class not in user_doc["balances"]["PaapTokens"]:
        user_doc["balances"]["PaapTokens"][severity_class] = 0
        
    # Add Paap tokens to the appropriate severity class
    user_doc["balances"]["PaapTokens"][severity_class] += paap_value
    
    return user_doc, severity_class, paap_value

def apply_rnanubandhan_tokens(user_doc, severity, value):
    """
    Apply Rnanubandhan tokens to a user's balance based on severity.
    
    Args:
        user_doc (dict): User document from database
        severity (str): The severity class ('minor', 'medium', 'major')
        value (float): The Rnanubandhan value to add
        
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
        
    # Add Rnanubandhan tokens to the appropriate severity class
    user_doc["balances"]["Rnanubandhan"][severity] += value
    
    # Calculate actual value with multiplier
    multiplier = TOKEN_ATTRIBUTES["Rnanubandhan"][severity]["multiplier"]
    actual_value = value * multiplier
    
    return user_doc, actual_value

def get_total_paap_score(user_doc):
    """
    Calculate the total weighted Paap score for a user.
    
    Args:
        user_doc (dict): User document from database
        
    Returns:
        float: Total weighted Paap score
    """
    if "PaapTokens" not in user_doc["balances"]:
        return 0
        
    paap_tokens = user_doc["balances"]["PaapTokens"]
    total_score = 0
    
    for severity, amount in paap_tokens.items():
        multiplier = TOKEN_ATTRIBUTES["PaapTokens"][severity]["multiplier"]
        total_score += amount * multiplier
        
    return total_score