import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import json
from utils.karma_schema import *
from utils.paap import apply_rnanubandhan_tokens

def get_test_user():
    """Get a fresh test user document"""
    return {
        "user_id": "test_user_001",
        "balances": {},
        "last_decay": None
    }

def test_dridha_adridha_karma():
    """Test DridhaKarma and AdridhaKarma functions"""
    user = get_test_user()
    
    # Test DridhaKarma
    user = apply_dridha_adridha_karma(user, 'DridhaKarma', 50)
    assert user['balances']['DridhaKarma'] == 50, "DridhaKarma not applied correctly"
    
    # Test AdridhaKarma
    user = apply_dridha_adridha_karma(user, 'AdridhaKarma', 30)
    assert user['balances']['AdridhaKarma'] == 30, "AdridhaKarma not applied correctly"
    
    print("✓ DridhaKarma and AdridhaKarma tests passed")

def test_sanchita_prarabdha_karma():
    """Test SanchitaKarma and PrarabdhaKarma functions"""
    user = get_test_user()
    
    # Test SanchitaKarma
    user = apply_sanchita_karma(user, 100)
    assert user['balances']['SanchitaKarma'] == 100, "SanchitaKarma not applied correctly"
    
    # Test PrarabdhaKarma
    user = apply_prarabdha_karma(user, 75)
    assert user['balances']['PrarabdhaKarma'] == 75, "PrarabdhaKarma not applied correctly"
    
    print("✓ SanchitaKarma and PrarabdhaKarma tests passed")

def test_rnanubandhan():
    """Test Rnanubandhan function"""
    user = get_test_user()
    
    # Test Rnanubandhan
    user, actual_value = apply_rnanubandhan_tokens(user, 'major', 25)
    assert user['balances']['Rnanubandhan']['major'] == 25, "Rnanubandhan not applied correctly"
    assert actual_value == 100, "Rnanubandhan actual value calculation incorrect"  # 25 * 4.0 multiplier
    
    print("✓ Rnanubandhan tests passed")

def test_karma_weights():
    """Test karma weights retrieval"""
    weights = get_karma_weights()
    
    # Check that all expected karma types are present
    expected_karma_types = ['DridhaKarma', 'AdridhaKarma', 'SanchitaKarma', 'PrarabdhaKarma']
    for karma_type in expected_karma_types:
        assert karma_type in weights, f"{karma_type} not found in weights"
    
    # Check specific weights
    assert weights['DridhaKarma'] == 0.8, "DridhaKarma weight incorrect"
    assert weights['AdridhaKarma'] == 0.3, "AdridhaKarma weight incorrect"
    
    print("✓ Karma weights tests passed")

def test_weighted_karma_score():
    """Test weighted karma score calculation"""
    user = get_test_user()
    
    # Apply various karma types
    user = apply_dridha_adridha_karma(user, 'DridhaKarma', 50)  # 50 * 0.8 = 40
    user = apply_dridha_adridha_karma(user, 'AdridhaKarma', 30)  # 30 * 0.3 = 9
    user = apply_sanchita_karma(user, 100)  # 100 * 1.0 = 100
    user = apply_prarabdha_karma(user, 75)  # 75 * 1.0 = 75
    user, _ = apply_rnanubandhan_tokens(user, 'major', 25)  # 25 (not multiplied here)
    
    # Let's debug the calculation
    weights = get_karma_weights()
    print(f"Weights: {weights}")
    print(f"User balances: {user['balances']}")
    
    # Calculate expected score manually:
    # DridhaKarma: 50 * 0.8 = 40
    # AdridhaKarma: 30 * 0.3 = 9
    # SanchitaKarma: 100 * 1.0 = 100
    # PrarabdhaKarma: 75 * 1.0 = 75
    # Rnanubandhan: 25 * 4.0 = 100
    # Total: 40 + 9 + 100 + 75 + 100 = 324
    
    expected_score = 324
    calculated_score = calculate_weighted_karma_score(user)
    
    print(f"Expected score: {expected_score}")
    print(f"Calculated score: {calculated_score}")
    
    assert calculated_score == expected_score, f"Weighted karma score calculation incorrect. Expected: {expected_score}, Got: {calculated_score}"
    
    print("✓ Weighted karma score tests passed")

def test_karma_actions_dataset():
    """Test that the karma actions dataset is valid"""
    dataset_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'karma_actions_dataset.json')
    
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    
    assert 'karma_actions' in data, "karma_actions key not found in dataset"
    assert len(data['karma_actions']) > 0, "No actions found in dataset"
    
    # Check that each action has the required fields
    for action in data['karma_actions']:
        assert 'action' in action, "action field missing"
        assert 'karma_types' in action, "karma_types field missing"
        assert 'description' in action, "description field missing"
    
    print("✓ Karma actions dataset tests passed")

if __name__ == "__main__":
    print("Running karma schema tests...")
    
    test_dridha_adridha_karma()
    test_sanchita_prarabdha_karma()
    test_rnanubandhan()
    test_karma_weights()
    test_weighted_karma_score()
    test_karma_actions_dataset()
    
    print("\n🎉 All tests passed!")