"""
Test suite for Rnanubandhan functionality
"""

import sys
import os
import pytest
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.rnanubandhan import RnanubandhanManager
from database import users_col, rnanubandhan_col

# Test data
test_user1 = {
    "user_id": "test_user_001",
    "role": "learner",
    "balances": {
        "DharmaPoints": 50,
        "SevaPoints": 30,
        "PunyaTokens": 20
    }
}

test_user2 = {
    "user_id": "test_user_002",
    "role": "learner",
    "balances": {
        "DharmaPoints": 40,
        "SevaPoints": 25,
        "PunyaTokens": 15
    }
}

def setup_test_users():
    """Set up test users in the database"""
    # Clear existing test users
    users_col.delete_many({"user_id": {"$in": ["test_user_001", "test_user_002"]}})
    
    # Insert test users
    users_col.insert_many([test_user1, test_user2])

def teardown_test_data():
    """Clean up test data"""
    # Remove test users
    users_col.delete_many({"user_id": {"$in": ["test_user_001", "test_user_002"]}})
    
    # Remove test relationships
    rnanubandhan_col.delete_many({
        "$or": [
            {"debtor_id": {"$in": ["test_user_001", "test_user_002"]}},
            {"receiver_id": {"$in": ["test_user_001", "test_user_002"]}}
        ]
    })

def test_create_debt_relationship():
    """Test creating a karmic debt relationship"""
    # Setup
    setup_test_users()
    
    try:
        # Create Rnanubandhan manager
        manager = RnanubandhanManager()
        
        # Create a debt relationship
        relationship = manager.create_debt_relationship(
            debtor_id="test_user_001",
            receiver_id="test_user_002",
            action_type="harm_action",
            severity="medium",
            amount=25.0,
            description="Caused harm to test_user_002"
        )
        
        # Assertions
        assert relationship["debtor_id"] == "test_user_001"
        assert relationship["receiver_id"] == "test_user_002"
        assert relationship["action_type"] == "harm_action"
        assert relationship["severity"] == "medium"
        assert relationship["amount"] == 25.0
        assert relationship["description"] == "Caused harm to test_user_002"
        assert relationship["status"] == "active"
        assert "_id" in relationship
        
    finally:
        # Teardown
        teardown_test_data()

def test_get_user_debts():
    """Test getting user debts"""
    # Setup
    setup_test_users()
    
    try:
        # Create Rnanubandhan manager
        manager = RnanubandhanManager()
        
        # Create a debt relationship
        relationship = manager.create_debt_relationship(
            debtor_id="test_user_001",
            receiver_id="test_user_002",
            action_type="harm_action",
            severity="medium",
            amount=25.0,
            description="Caused harm to test_user_002"
        )
        
        # Get user debts
        debts = manager.get_user_debts("test_user_001")
        
        # Assertions
        assert len(debts) == 1
        assert debts[0]["debtor_id"] == "test_user_001"
        assert debts[0]["receiver_id"] == "test_user_002"
        assert debts[0]["amount"] == 25.0
        
    finally:
        # Teardown
        teardown_test_data()

def test_get_user_credits():
    """Test getting user credits"""
    # Setup
    setup_test_users()
    
    try:
        # Create Rnanubandhan manager
        manager = RnanubandhanManager()
        
        # Create a debt relationship
        relationship = manager.create_debt_relationship(
            debtor_id="test_user_001",
            receiver_id="test_user_002",
            action_type="harm_action",
            severity="medium",
            amount=25.0,
            description="Caused harm to test_user_002"
        )
        
        # Get user credits
        credits = manager.get_user_credits("test_user_002")
        
        # Assertions
        assert len(credits) == 1
        assert credits[0]["debtor_id"] == "test_user_001"
        assert credits[0]["receiver_id"] == "test_user_002"
        assert credits[0]["amount"] == 25.0
        
    finally:
        # Teardown
        teardown_test_data()

def test_get_network_summary():
    """Test getting network summary"""
    # Setup
    setup_test_users()
    
    try:
        # Create Rnanubandhan manager
        manager = RnanubandhanManager()
        
        # Create debt relationships
        manager.create_debt_relationship(
            debtor_id="test_user_001",
            receiver_id="test_user_002",
            action_type="harm_action",
            severity="medium",
            amount=25.0,
            description="Caused harm to test_user_002"
        )
        
        manager.create_debt_relationship(
            debtor_id="test_user_002",
            receiver_id="test_user_001",
            action_type="help_action",
            severity="minor",
            amount=10.0,
            description="Helped test_user_001"
        )
        
        # Get network summary
        summary = manager.get_network_summary("test_user_001")
        
        # Assertions
        assert summary["user_id"] == "test_user_001"
        assert summary["total_debt"] == 25.0
        assert summary["total_credit"] == 10.0
        assert summary["net_position"] == -15.0  # 10 - 25 = -15
        assert summary["active_debts"] == 1
        assert summary["active_credits"] == 1
        
    finally:
        # Teardown
        teardown_test_data()

def test_repay_debt():
    """Test repaying a karmic debt"""
    # Setup
    setup_test_users()
    
    try:
        # Create Rnanubandhan manager
        manager = RnanubandhanManager()
        
        # Create a debt relationship
        relationship = manager.create_debt_relationship(
            debtor_id="test_user_001",
            receiver_id="test_user_002",
            action_type="harm_action",
            severity="medium",
            amount=25.0,
            description="Caused harm to test_user_002"
        )
        
        # Repay part of the debt
        updated_relationship = manager.repay_debt(
            relationship_id=relationship["_id"],
            amount=10.0,
            repayment_method="atonement"
        )
        
        # Assertions
        assert updated_relationship["amount"] == 15.0  # 25 - 10 = 15
        assert updated_relationship["status"] == "active"
        assert len(updated_relationship["repayment_history"]) == 1
        assert updated_relationship["repayment_history"][0]["amount"] == 10.0
        assert updated_relationship["repayment_history"][0]["method"] == "atonement"
        
        # Repay the remaining debt
        final_relationship = manager.repay_debt(
            relationship_id=relationship["_id"],
            amount=15.0,
            repayment_method="service"
        )
        
        # Assertions
        assert final_relationship["amount"] == 0.0
        assert final_relationship["status"] == "repaid"
        assert len(final_relationship["repayment_history"]) == 2
        assert final_relationship["repayment_history"][1]["amount"] == 15.0
        assert final_relationship["repayment_history"][1]["method"] == "service"
        
    finally:
        # Teardown
        teardown_test_data()

def test_transfer_debt():
    """Test transferring a karmic debt"""
    # Setup
    setup_test_users()
    
    # Add a third test user
    test_user3 = {
        "user_id": "test_user_003",
        "role": "learner",
        "balances": {
            "DharmaPoints": 30,
            "SevaPoints": 20,
            "PunyaTokens": 10
        }
    }
    users_col.insert_one(test_user3)
    
    try:
        # Create Rnanubandhan manager
        manager = RnanubandhanManager()
        
        # Create a debt relationship
        relationship = manager.create_debt_relationship(
            debtor_id="test_user_001",
            receiver_id="test_user_002",
            action_type="harm_action",
            severity="medium",
            amount=25.0,
            description="Caused harm to test_user_002"
        )
        
        # Transfer the debt to test_user_003
        new_relationship = manager.transfer_debt(
            relationship_id=relationship["_id"],
            new_debtor_id="test_user_003"
        )
        
        # Assertions
        assert new_relationship["debtor_id"] == "test_user_003"
        assert new_relationship["receiver_id"] == "test_user_002"
        assert new_relationship["amount"] == 25.0
        assert new_relationship["status"] == "active"
        
        # Check that the original relationship is marked as transferred
        original_relationship = manager.get_relationship_by_id(relationship["_id"])
        assert original_relationship["status"] == "transferred"
        
    finally:
        # Teardown
        teardown_test_data()
        users_col.delete_one({"user_id": "test_user_003"})

def test_error_cases():
    """Test error cases"""
    # Setup
    setup_test_users()
    
    try:
        # Create Rnanubandhan manager
        manager = RnanubandhanManager()
        
        # Test creating debt with same debtor and receiver
        try:
            manager.create_debt_relationship(
                debtor_id="test_user_001",
                receiver_id="test_user_001",  # Same as debtor
                action_type="harm_action",
                severity="medium",
                amount=25.0
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected
        
        # Test creating debt with non-existent user
        try:
            manager.create_debt_relationship(
                debtor_id="non_existent_user",
                receiver_id="test_user_002",
                action_type="harm_action",
                severity="medium",
                amount=25.0
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected
        
    finally:
        # Teardown
        teardown_test_data()

if __name__ == "__main__":
    print("Running Rnanubandhan tests...")
    
    test_create_debt_relationship()
    print("✓ Create debt relationship test passed")
    
    test_get_user_debts()
    print("✓ Get user debts test passed")
    
    test_get_user_credits()
    print("✓ Get user credits test passed")
    
    test_get_network_summary()
    print("✓ Get network summary test passed")
    
    test_repay_debt()
    print("✓ Repay debt test passed")
    
    test_transfer_debt()
    print("✓ Transfer debt test passed")
    
    test_error_cases()
    print("✓ Error cases test passed")
    
    print("\n🎉 All Rnanubandhan tests passed!")