"""
Test suite for Behavioral State Normalization
"""
import sys
import os
import uuid
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from routes.normalization import normalize_single_state, StateSchema
from routes.normalization import NormalizeStateRequest

def test_normalize_single_state_finance():
    """Test normalizing a finance module state"""
    request = NormalizeStateRequest(
        module="finance",
        action_type="transaction",
        raw_value=100.0
    )
    
    normalized = normalize_single_state(request)
    
    # Check that we get a valid StateSchema back
    assert isinstance(normalized, StateSchema)
    assert normalized.module == "finance"
    assert normalized.action_type == "transaction"
    assert normalized.weight == 1.0  # Default weight for finance
    assert normalized.feedback_value == 100.0  # 100 * 1.0
    assert isinstance(uuid.UUID(normalized.state_id), uuid.UUID)
    assert isinstance(normalized.timestamp, str)

def test_normalize_single_state_gurukul():
    """Test normalizing a gurukul module state"""
    request = NormalizeStateRequest(
        module="gurukul",
        action_type="lesson_completed",
        raw_value=85.5
    )
    
    normalized = normalize_single_state(request)
    
    # Check that we get a valid StateSchema back
    assert isinstance(normalized, StateSchema)
    assert normalized.module == "gurukul"
    assert normalized.action_type == "lesson_completed"
    assert normalized.weight == 1.3  # Default weight for gurukul from context_weights.json
    assert normalized.feedback_value == 85.5 * 1.3  # 85.5 * 1.3
    assert isinstance(uuid.UUID(normalized.state_id), uuid.UUID)
    assert isinstance(normalized.timestamp, str)

def test_normalize_single_state_game():
    """Test normalizing a game module state"""
    request = NormalizeStateRequest(
        module="game",
        action_type="level_completed",
        raw_value=75.0
    )
    
    normalized = normalize_single_state(request)
    
    # Check that we get a valid StateSchema back
    assert isinstance(normalized, StateSchema)
    assert normalized.module == "game"
    assert normalized.action_type == "level_completed"
    assert normalized.weight == 1.2  # Default weight for game from context_weights.json
    assert normalized.feedback_value == 75.0 * 1.2  # 75.0 * 1.2
    assert isinstance(uuid.UUID(normalized.state_id), uuid.UUID)
    assert isinstance(normalized.timestamp, str)

def test_normalize_single_state_insight():
    """Test normalizing an insight module state"""
    request = NormalizeStateRequest(
        module="insight",
        action_type="meditation_session",
        raw_value=60.0
    )
    
    normalized = normalize_single_state(request)
    
    # Check that we get a valid StateSchema back
    assert isinstance(normalized, StateSchema)
    assert normalized.module == "insight"
    assert normalized.action_type == "meditation_session"
    assert normalized.weight == 1.1  # Default weight for insight from context_weights.json
    assert normalized.feedback_value == 60.0 * 1.1  # 60.0 * 1.1
    assert isinstance(uuid.UUID(normalized.state_id), uuid.UUID)
    assert isinstance(normalized.timestamp, str)

def test_normalize_single_state_invalid_module():
    """Test normalizing a state with an invalid module (should use default weight)"""
    request = NormalizeStateRequest(
        module="unknown_module",
        action_type="test_action",
        raw_value=50.0
    )
    
    normalized = normalize_single_state(request)
    
    # Check that we get a valid StateSchema back with default weight
    assert isinstance(normalized, StateSchema)
    assert normalized.module == "unknown_module"
    assert normalized.action_type == "test_action"
    assert normalized.weight == 1.0  # Default weight when module not found
    assert normalized.feedback_value == 50.0  # 50.0 * 1.0
    assert isinstance(uuid.UUID(normalized.state_id), uuid.UUID)
    assert isinstance(normalized.timestamp, str)

if __name__ == "__main__":
    print("Running Behavioral State Normalization Tests...")
    
    test_normalize_single_state_finance()
    print("✓ Finance module normalization test passed")
    
    test_normalize_single_state_gurukul()
    print("✓ Gurukul module normalization test passed")
    
    test_normalize_single_state_game()
    print("✓ Game module normalization test passed")
    
    test_normalize_single_state_insight()
    print("✓ Insight module normalization test passed")
    
    test_normalize_single_state_invalid_module()
    print("✓ Invalid module normalization test passed")
    
    print("\n🎉 All normalization tests passed!")