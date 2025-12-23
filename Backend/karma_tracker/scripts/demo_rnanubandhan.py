#!/usr/bin/env python3
"""
Test script for Rnanubandhan functionality
This script demonstrates the core features of the Rnanubandhan system.
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import users_col
from utils.rnanubandhan import rnanubandhan_manager

# Base URL for the API
BASE_URL = "http://localhost:8000"

def create_test_users():
    """Create test users in the database"""
    print("Creating test users...")
    
    # Test users
    users = [
        {
            "user_id": "arjun_123",
            "role": "human",
            "balances": {
                "DharmaPoints": 250,
                "SevaPoints": 180,
                "PunyaTokens": 200,
                "PaapTokens": {"minor": 5, "medium": 2}
            }
        },
        {
            "user_id": "raj_456",
            "role": "human",
            "balances": {
                "DharmaPoints": 200,
                "SevaPoints": 150,
                "PunyaTokens": 180,
                "PaapTokens": {"minor": 3, "medium": 1}
            }
        },
        {
            "user_id": "priya_789",
            "role": "human",
            "balances": {
                "DharmaPoints": 300,
                "SevaPoints": 220,
                "PunyaTokens": 250,
                "PaapTokens": {"minor": 2}
            }
        }
    ]
    
    # Clear existing test users
    user_ids = [user["user_id"] for user in users]
    users_col.delete_many({"user_id": {"$in": user_ids}})
    
    # Insert test users
    users_col.insert_many(users)
    print(f"Created {len(users)} test users")

def test_create_debt_relationship():
    """Test creating a karmic debt relationship"""
    print("\n=== Testing Create Debt Relationship ===")
    
    try:
        # Create a debt relationship between Arjun and Raj
        relationship = rnanubandhan_manager.create_debt_relationship(
            debtor_id="arjun_123",
            receiver_id="raj_456",
            action_type="harm_action",
            severity="medium",
            amount=25.0,
            description="Caused emotional harm during business disagreement"
        )
        
        print("Created debt relationship:")
        print(json.dumps(relationship, indent=2, default=str))
        return relationship["_id"]
        
    except Exception as e:
        print(f"Error creating debt relationship: {e}")
        return None

def test_get_network():
    """Test getting a user's Rnanubandhan network"""
    print("\n=== Testing Get Network ===")
    
    try:
        # Get Arjun's network
        network = rnanubandhan_manager.get_network_summary("arjun_123")
        print("Arjun's Rnanubandhan network:")
        print(json.dumps(network, indent=2))
        
        # Get Raj's network
        network = rnanubandhan_manager.get_network_summary("raj_456")
        print("\nRaj's Rnanubandhan network:")
        print(json.dumps(network, indent=2))
        
    except Exception as e:
        print(f"Error getting network: {e}")

def test_api_endpoints():
    """Test the API endpoints"""
    print("\n=== Testing API Endpoints ===")
    
    try:
        # Test getting user's full network
        response = requests.get(f"{BASE_URL}/api/v1/rnanubandhan/arjun_123")
        if response.status_code == 200:
            print("GET /api/v1/rnanubandhan/{user_id} - SUCCESS")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"GET /api/v1/rnanubandhan/{{user_id}} - FAILED: {response.status_code}")
            print(response.text)
            
        # Test getting user's debts
        response = requests.get(f"{BASE_URL}/api/v1/rnanubandhan/arjun_123/debts")
        if response.status_code == 200:
            print("\nGET /api/v1/rnanubandhan/{user_id}/debts - SUCCESS")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"GET /api/v1/rnanubandhan/{{user_id}}/debts - FAILED: {response.status_code}")
            print(response.text)
            
        # Test getting user's credits
        response = requests.get(f"{BASE_URL}/api/v1/rnanubandhan/raj_456/credits")
        if response.status_code == 200:
            print("\nGET /api/v1/rnanubandhan/{user_id}/credits - SUCCESS")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"GET /api/v1/rnanubandhan/{{user_id}}/credits - FAILED: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error testing API endpoints: {e}")

def test_repay_debt(relationship_id):
    """Test repaying a karmic debt"""
    print("\n=== Testing Repay Debt ===")
    
    if not relationship_id:
        print("No relationship ID provided, skipping repayment test")
        return
        
    try:
        # Repay part of the debt
        updated_relationship = rnanubandhan_manager.repay_debt(
            relationship_id=relationship_id,
            amount=10.0,
            repayment_method="atonement"
        )
        
        print("Partial debt repayment:")
        print(json.dumps(updated_relationship, indent=2, default=str))
        
        # Repay the remaining debt
        final_relationship = rnanubandhan_manager.repay_debt(
            relationship_id=relationship_id,
            amount=15.0,
            repayment_method="service"
        )
        
        print("\nFull debt repayment:")
        print(json.dumps(final_relationship, indent=2, default=str))
        
    except Exception as e:
        print(f"Error repaying debt: {e}")

def test_transfer_debt(relationship_id):
    """Test transferring a karmic debt"""
    print("\n=== Testing Transfer Debt ===")
    
    if not relationship_id:
        print("No relationship ID provided, skipping transfer test")
        return
        
    try:
        # Transfer the debt to Priya
        new_relationship = rnanubandhan_manager.transfer_debt(
            relationship_id=relationship_id,
            new_debtor_id="priya_789"
        )
        
        print("Debt transfer to Priya:")
        print(json.dumps(new_relationship, indent=2, default=str))
        
        return new_relationship["_id"]
        
    except Exception as e:
        print(f"Error transferring debt: {e}")
        return None

def test_create_debt_via_api():
    """Test creating a debt relationship via API"""
    print("\n=== Testing Create Debt via API ===")
    
    try:
        # Create debt data
        debt_data = {
            "debtor_id": "priya_789",
            "receiver_id": "arjun_123",
            "action_type": "help_action",
            "severity": "minor",
            "amount": 15.0,
            "description": "Helped with business project"
        }
        
        # Make API request
        response = requests.post(
            f"{BASE_URL}/api/v1/rnanubandhan/create-debt",
            json=debt_data
        )
        
        if response.status_code == 200:
            print("Create debt via API - SUCCESS")
            print(json.dumps(response.json(), indent=2))
            return response.json()["relationship"]["_id"]
        else:
            print(f"Create debt via API - FAILED: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"Error creating debt via API: {e}")
        return None

def test_log_action_with_relationship():
    """Test logging an action that creates an Rnanubandhan relationship"""
    print("\n=== Testing Log Action with Rnanubandhan Relationship ===")
    
    try:
        # Log a harmful action that affects another user
        action_data = {
            "user_id": "arjun_123",
            "action": "cheat",
            "role": "human",
            "note": "Tried to deceive Raj in business deal",
            "affected_user_id": "raj_456",
            "relationship_description": "Attempted business deception"
        }
        
        # Make API request to log action
        response = requests.post(
            f"{BASE_URL}/v1/karma/log-action/",
            json=action_data
        )
        
        if response.status_code == 200:
            print("Log action with relationship - SUCCESS")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Log action with relationship - FAILED: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error logging action with relationship: {e}")

def cleanup_test_data():
    """Clean up test data"""
    print("\n=== Cleaning up test data ===")
    
    # Remove test users
    user_ids = ["arjun_123", "raj_456", "priya_789"]
    users_col.delete_many({"user_id": {"$in": user_ids}})
    
    # Remove test relationships
    from database import rnanubandhan_col
    rnanubandhan_col.delete_many({
        "$or": [
            {"debtor_id": {"$in": user_ids}},
            {"receiver_id": {"$in": user_ids}}
        ]
    })
    
    print("Test data cleaned up")

def main():
    """Main test function"""
    print("Rnanubandhan Test Script")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("WARNING: Server health check failed. Some API tests may fail.")
    except Exception as e:
        print(f"WARNING: Cannot connect to server at {BASE_URL}. Some API tests may fail.")
    
    try:
        # Create test users
        create_test_users()
        
        # Test creating debt relationship
        relationship_id = test_create_debt_relationship()
        
        # Test getting network
        test_get_network()
        
        # Test API endpoints
        test_api_endpoints()
        
        # Test repaying debt
        test_repay_debt(relationship_id)
        
        # Test transferring debt
        new_relationship_id = test_transfer_debt(relationship_id)
        
        # Test creating debt via API
        api_relationship_id = test_create_debt_via_api()
        
        # Test logging action with relationship
        test_log_action_with_relationship()
        
        print("\n" + "=" * 50)
        print("Rnanubandhan tests completed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        # Clean up test data
        cleanup_test_data()

if __name__ == "__main__":
    main()