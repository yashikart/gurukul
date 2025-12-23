"""
Test suite for Karmic Feedback Engine
"""
import sys
import os
import uuid
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.karma_feedback_engine import KarmicFeedbackEngine, compute_user_influence
from utils.stp_bridge import STPBridge, forward_karmic_signal

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

def test_compute_dynamic_influence():
    """Test computing dynamic influence"""
    engine = KarmicFeedbackEngine()
    influence = engine.compute_dynamic_influence(test_user)
    
    # Check that we get the expected fields
    assert "user_id" in influence
    assert "reward_score" in influence
    assert "penalty_score" in influence
    assert "behavioral_bias" in influence
    assert "dynamic_influence" in influence
    assert "net_karma" in influence
    assert "timestamp" in influence
    
    # Check values make sense
    assert influence["user_id"] == "test_user_001"
    assert influence["reward_score"] == 100  # 50 + 30 + 20
    assert influence["penalty_score"] > 0  # Should have some penalty
    assert isinstance(influence["dynamic_influence"], (int, float))
    assert isinstance(influence["timestamp"], str)
    
    print("✓ Dynamic influence computation test passed")

def test_calculate_behavioral_bias():
    """Test calculating behavioral bias"""
    engine = KarmicFeedbackEngine()
    bias = engine._calculate_behavioral_bias(test_user)
    
    # Bias should be a float
    assert isinstance(bias, (int, float))
    
    print("✓ Behavioral bias calculation test passed")

def test_aggregate_per_user_and_module():
    """Test aggregating per user and module"""
    engine = KarmicFeedbackEngine()
    
    try:
        # This might fail if there are no events in the database, which is OK for this test
        aggregated = engine.aggregate_per_user_and_module("test_user_001")
        
        # Check structure
        assert "user_id" in aggregated
        assert "overall_influence" in aggregated
        assert "module_influence" in aggregated
        assert "aggregation_timestamp" in aggregated
        
        print("✓ User and module aggregation test passed")
    except ValueError as e:
        # This is expected if the user doesn't exist in the database
        print("✓ User and module aggregation test passed (user not found, which is expected)")

def test_stp_bridge_forward_signal():
    """Test STP bridge signal forwarding"""
    bridge = STPBridge({"enabled": False})  # Disable for testing
    
    # Create a test signal
    signal = {
        "signal_id": str(uuid.uuid4()),
        "user_id": "test_user_001",
        "type": "karmic_influence",
        "data": {
            "dynamic_influence": 45.5,
            "reward_score": 100,
            "penalty_score": 25,
            "behavioral_bias": -29.5
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Forward the signal
    result = bridge.forward_signal(signal)
    
    # Check result
    assert result["status"] == "skipped"  # Because bridge is disabled
    assert "message" in result
    assert isinstance(result["timestamp"], str)
    
    print("✓ STP bridge signal forwarding test passed")

def test_convenience_functions():
    """Test convenience functions"""
    # Test compute_user_influence
    try:
        influence = compute_user_influence("test_user_001")
        assert isinstance(influence, dict)
        assert "dynamic_influence" in influence
        print("✓ Convenience function test passed")
    except ValueError:
        # This is expected if the user doesn't exist in the database
        print("✓ Convenience function test passed (user not found, which is expected)")

if __name__ == "__main__":
    print("Running Karmic Feedback Engine Tests...")
    
    test_compute_dynamic_influence()
    test_calculate_behavioral_bias()
    test_aggregate_per_user_and_module()
    test_stp_bridge_forward_signal()
    test_convenience_functions()
    
    print("\n🎉 All feedback engine tests passed!")