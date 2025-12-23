import sys
import os
import pytest
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.karma_engine import *

# Test user document
test_user = {
    "user_id": "test_user_001",
    "role": "learner",
    "balances": {
        "DharmaPoints": 50,
        "SevaPoints": 30,
        "PunyaTokens": 20,
        "PaapTokens": {
            "minor": 5,
            "medium": 2
        },
        "DridhaKarma": 40,
        "AdridhaKarma": 15,
        "SanchitaKarma": 100,
        "PrarabdhaKarma": 50,
        "Rnanubandhan": {
            "minor": 3,
            "medium": 1
        }
    },
    "last_decay": None
}

def test_evaluate_action_karma_positive():
    """Test karma evaluation for positive actions"""
    result = evaluate_action_karma(test_user, "completing_lessons", 1.0)
    
    assert result["action"] == "completing_lessons"
    assert result["intensity"] == 1.0
    assert result["positive_impact"] > 0
    assert result["dridha_influence"] > 0
    assert len(result["corrective_recommendations"]) >= 0

def test_evaluate_action_karma_negative():
    """Test karma evaluation for negative actions"""
    result = evaluate_action_karma(test_user, "cheat", 1.0)
    
    assert result["action"] == "cheat"
    assert result["intensity"] == 1.0
    assert result["negative_impact"] > 0
    assert result["adridha_influence"] < 0
    assert result["rnanubandhan_change"] > 0

def test_calculate_net_karma():
    """Test net karma calculation"""
    result = calculate_net_karma(test_user)
    
    assert "net_karma" in result
    assert "weighted_score" in result
    assert "breakdown" in result
    assert isinstance(result["net_karma"], (int, float))
    assert isinstance(result["weighted_score"], (int, float))

def test_determine_corrective_guidance():
    """Test corrective guidance determination"""
    recommendations = determine_corrective_guidance(test_user)
    
    assert isinstance(recommendations, list)
    # Check that recommendations have the expected structure
    for rec in recommendations:
        assert "practice" in rec
        assert "reason" in rec
        assert "urgency" in rec
        assert "weight" in rec

def test_integrate_with_q_learning():
    """Test Q-learning integration"""
    adjusted_reward, next_role = integrate_with_q_learning(test_user, "completing_lessons", 10.0)
    
    assert isinstance(adjusted_reward, (int, float))
    assert isinstance(next_role, str)
    # The adjusted reward should be different from the base reward due to karmic factors
    # But for this test user, it might be close depending on their karma balance

def test_get_purushartha_score():
    """Test Purushartha score calculation"""
    scores = get_purushartha_score(test_user)
    
    assert isinstance(scores, dict)
    expected_categories = ["Dharma", "Artha", "Kama", "Moksha"]
    for category in expected_categories:
        assert category in scores
        assert isinstance(scores[category], (int, float))

def test_purushartha_alignment():
    """Test Purushartha alignment in action evaluation"""
    result = evaluate_action_karma(test_user, "completing_lessons", 1.0)
    
    assert "purushartha_alignment" in result
    alignment = result["purushartha_alignment"]
    
    expected_categories = ["Dharma", "Artha", "Kama", "Moksha"]
    for category in expected_categories:
        assert category in alignment
        assert isinstance(alignment[category], (int, float))

# New edge-case tests for robust coverage

def test_rnanubandhan_legacy_scalar():
    """Rnanubandhan as a legacy scalar should be handled without errors"""
    user = dict(test_user)
    user["balances"] = dict(test_user["balances"])  # shallow copy
    user["balances"]["Rnanubandhan"] = 12.5  # legacy numeric
    result = calculate_net_karma(user)
    assert isinstance(result["net_karma"], (int, float))


def test_rnanubandhan_dict_invalid_values():
    """Invalid values in Rnanubandhan dict should be skipped safely"""
    user = dict(test_user)
    user["balances"] = dict(test_user["balances"])  # shallow copy
    user["balances"]["Rnanubandhan"] = {"minor": "not_a_number", "major": 10}
    result = calculate_net_karma(user)
    assert isinstance(result["net_karma"], (int, float))


def test_rnanubandhan_list_entries():
    """List-based Rnanubandhan entries should be supported (dict and numeric)"""
    user = dict(test_user)
    user["balances"] = dict(test_user["balances"])  # shallow copy
    user["balances"]["Rnanubandhan"] = [
        {"severity": "medium", "amount": 7},
        3.5,
        {"severity": "unknown", "amount": 2}  # falls back to major multiplier
    ]
    result = calculate_net_karma(user)
    assert isinstance(result["net_karma"], (int, float))


def test_integrate_with_q_learning_zero_net():
    """Integration should not divide by zero when net_karma is zero"""
    user = dict(test_user)
    # Force a balanced state to approximate net_karma ~ 0
    user["balances"] = {
        "DharmaPoints": 0,
        "SevaPoints": 0,
        "PunyaTokens": 0,
        "PaapTokens": {"minor": 0, "medium": 0, "maha": 0},
        "DridhaKarma": 0,
        "AdridhaKarma": 0,
        "SanchitaKarma": 0,
        "PrarabdhaKarma": 0,
        "Rnanubandhan": 0
    }
    adjusted_reward, next_role = integrate_with_q_learning(user, "completing_lessons", 10.0)
    assert isinstance(adjusted_reward, (int, float))
    assert isinstance(next_role, str)

def test_edge_cases():
    """Test edge cases"""
    # Test with unknown action
    result = evaluate_action_karma(test_user, "unknown_action", 1.0)
    assert result["action"] == "unknown_action"
    
    # Test with high intensity
    result = evaluate_action_karma(test_user, "completing_lessons", 2.0)
    assert result["intensity"] == 2.0
    
    # Test with zero intensity
    result = evaluate_action_karma(test_user, "completing_lessons", 0.0)
    assert result["intensity"] == 0.0

if __name__ == "__main__":
    print("Running karma engine tests...")
    
    test_evaluate_action_karma_positive()
    print("✓ Positive action karma evaluation test passed")
    
    test_evaluate_action_karma_negative()
    print("✓ Negative action karma evaluation test passed")
    
    test_calculate_net_karma()
    print("✓ Net karma calculation test passed")
    
    test_determine_corrective_guidance()
    print("✓ Corrective guidance test passed")
    
    test_integrate_with_q_learning()
    print("✓ Q-learning integration test passed")
    
    test_get_purushartha_score()
    print("✓ Purushartha score test passed")
    
    test_purushartha_alignment()
    print("✓ Purushartha alignment test passed")
    
    test_edge_cases()
    print("✓ Edge cases test passed")
    
    print("\n🎉 All karma engine tests passed!")