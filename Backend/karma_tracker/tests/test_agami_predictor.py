"""
Test suite for Agami Karma Predictor functionality
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.agami_predictor import AgamiKarmaPredictor
from database import users_col

# Test data
test_user = {
    "user_id": "test_user_001",
    "role": "learner",
    "balances": {
        "DharmaPoints": 100,
        "SevaPoints": 80,
        "PunyaTokens": 70,
        "PaapTokens": {
            "minor": 25,
            "medium": 50
        }
    }
}

def setup_test_user():
    """Set up test user in the database"""
    # Clear existing test user
    users_col.delete_one({"user_id": "test_user_001"})
    
    # Insert test user
    users_col.insert_one(test_user)

def teardown_test_data():
    """Clean up test data"""
    # Remove test user
    users_col.delete_one({"user_id": "test_user_001"})

def test_agami_predictor_initialization():
    """Test AgamiKarmaPredictor initialization"""
    try:
        predictor = AgamiKarmaPredictor()
        assert predictor is not None
        print("✓ AgamiKarmaPredictor initialization test passed")
        return True
    except Exception as e:
        print(f"✗ AgamiKarmaPredictor initialization test failed: {e}")
        return False

def test_predict_agami_karma():
    """Test Agami karma prediction"""
    # Setup
    setup_test_user()
    
    try:
        # Create predictor
        predictor = AgamiKarmaPredictor()
        
        # Test prediction
        prediction = predictor.predict_agami_karma("test_user_001")
        
        # Assertions
        assert "user_id" in prediction
        assert "timestamp" in prediction
        assert "current_state" in prediction
        assert "q_learning_predictions" in prediction
        assert "agami_karma" in prediction
        assert "recommendations" in prediction
        
        # Check current state structure
        current_state = prediction["current_state"]
        assert "net_karma" in current_state
        assert "merit_score" in current_state
        assert "paap_score" in current_state
        assert "role" in current_state
        assert "balances" in current_state
        
        # Check Q-learning predictions structure
        q_predictions = prediction["q_learning_predictions"]
        assert "best_actions" in q_predictions
        assert "role_progression" in q_predictions
        assert "confidence" in q_predictions
        
        # Check Agami karma structure
        agami_karma = prediction["agami_karma"]
        assert "projected_balances" in agami_karma
        assert "projected_merit_score" in agami_karma
        assert "projected_paap_score" in agami_karma
        assert "projected_net_karma" in agami_karma
        assert "projected_role" in agami_karma
        assert "expected_change" in agami_karma
        
        print("✓ Predict Agami Karma test passed")
        return True
        
    except Exception as e:
        print(f"✗ Predict Agami Karma test failed: {e}")
        return False
    finally:
        # Teardown
        teardown_test_data()

def test_predict_with_scenario():
    """Test Agami karma prediction with scenario"""
    # Setup
    setup_test_user()
    
    try:
        # Create predictor
        predictor = AgamiKarmaPredictor()
        
        # Test prediction with scenario
        scenario = {
            "context": {
                "environment": "gurukul",
                "role": "student",
                "goal": "learning"
            }
        }
        
        prediction = predictor.predict_agami_karma("test_user_001", scenario)
        
        # Assertions
        assert "context_aware_predictions" in prediction
        context_predictions = prediction["context_aware_predictions"]
        assert "context" in context_predictions
        assert "purushartha_modifiers" in context_predictions
        
        print("✓ Predict with Scenario test passed")
        return True
        
    except Exception as e:
        print(f"✗ Predict with Scenario test failed: {e}")
        return False
    finally:
        # Teardown
        teardown_test_data()

def test_context_weights():
    """Test context weights functionality"""
    try:
        # Create predictor
        predictor = AgamiKarmaPredictor()
        
        # Test getting non-existent context weights
        weights = predictor.get_context_weights("non_existent_context")
        assert isinstance(weights, dict)
        assert len(weights) == 0
        
        # Test updating context weights
        test_weights = {
            "dharma_weight": 1.5,
            "artha_weight": 1.2,
            "kama_weight": 0.8,
            "moksha_weight": 1.3
        }
        
        predictor.update_context_weights("test_context", test_weights)
        
        # Test getting updated context weights
        retrieved_weights = predictor.get_context_weights("test_context")
        assert retrieved_weights == test_weights
        
        print("✓ Context Weights test passed")
        return True
        
    except Exception as e:
        print(f"✗ Context Weights test failed: {e}")
        return False

def test_context_weights_file():
    """Test context weights file operations"""
    try:
        # Create predictor
        predictor = AgamiKarmaPredictor()
        
        # Check if context_weights.json exists and can be loaded
        assert hasattr(predictor, 'context_weights')
        assert isinstance(predictor.context_weights, dict)
        
        print("✓ Context Weights File test passed")
        return True
        
    except Exception as e:
        print(f"✗ Context Weights File test failed: {e}")
        return False

def test_error_handling():
    """Test error handling"""
    try:
        # Create predictor
        predictor = AgamiKarmaPredictor()
        
        # Test prediction for non-existent user
        try:
            predictor.predict_agami_karma("non_existent_user")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected
        
        print("✓ Error Handling test passed")
        return True
        
    except Exception as e:
        print(f"✗ Error Handling test failed: {e}")
        return False

def test_recommendations_generation():
    """Test recommendations generation"""
    # Setup
    setup_test_user()
    
    try:
        # Create predictor
        predictor = AgamiKarmaPredictor()
        
        # Test prediction
        prediction = predictor.predict_agami_karma("test_user_001")
        
        # Check recommendations
        recommendations = prediction["recommendations"]
        assert isinstance(recommendations, list)
        
        # Check recommendation structure
        if len(recommendations) > 0:
            rec = recommendations[0]
            assert "type" in rec
            assert "priority" in rec
            assert "action" in rec
            assert "reasoning" in rec
            assert "expected_benefit" in rec
        
        print("✓ Recommendations Generation test passed")
        return True
        
    except Exception as e:
        print(f"✗ Recommendations Generation test failed: {e}")
        return False
    finally:
        # Teardown
        teardown_test_data()

if __name__ == "__main__":
    print("Running Agami Karma Predictor tests...")
    print("=" * 50)
    
    tests = [
        test_agami_predictor_initialization,
        test_predict_agami_karma,
        test_predict_with_scenario,
        test_context_weights,
        test_context_weights_file,
        test_error_handling,
        test_recommendations_generation
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All Agami Karma Predictor tests passed!")
    else:
        print("⚠️  Some tests failed.")