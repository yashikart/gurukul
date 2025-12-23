#!/usr/bin/env python3
"""
Test script for Agami Karma Predictor functionality
This script demonstrates the core features of the Agami prediction system.
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import users_col
from utils.agami_predictor import agami_predictor

# Base URL for the API
BASE_URL = "http://localhost:8000"

def create_test_users():
    """Create test users in the database"""
    print("Creating test users...")
    
    # Test users
    users = [
        {
            "user_id": "arjun_123",
            "role": "student",
            "balances": {
                "DharmaPoints": 100,
                "SevaPoints": 80,
                "PunyaTokens": 70,
                "PaapTokens": {"minor": 25, "medium": 50}
            }
        },
        {
            "user_id": "raju_456",
            "role": "warrior",
            "balances": {
                "DharmaPoints": 120,
                "SevaPoints": 60,
                "PunyaTokens": 90,
                "PaapTokens": {"minor": 30, "medium": 40}
            }
        }
    ]
    
    # Clear existing test users
    user_ids = [user["user_id"] for user in users]
    users_col.delete_many({"user_id": {"$in": user_ids}})
    
    # Insert test users
    users_col.insert_many(users)
    print(f"Created {len(users)} test users")

def test_direct_prediction():
    """Test Agami prediction directly through function calls"""
    print("\n=== Testing Direct Agami Prediction ===")
    
    try:
        # Test prediction for Arjun (student in Gurukul)
        prediction = agami_predictor.predict_agami_karma(
            user_id="arjun_123",
            scenario={
                "context": {
                    "environment": "gurukul",
                    "role": "student",
                    "goal": "learning"
                }
            }
        )
        
        print("Agami prediction for student in Gurukul:")
        print(json.dumps(prediction, indent=2, default=str))
        
        # Test prediction for Raju (warrior in Game Realm)
        prediction = agami_predictor.predict_agami_karma(
            user_id="raju_456",
            scenario={
                "context": {
                    "environment": "game_realm",
                    "role": "warrior",
                    "goal": "conquest"
                }
            }
        )
        
        print("\nAgami prediction for warrior in Game Realm:")
        print(json.dumps(prediction, indent=2, default=str))
        
    except Exception as e:
        print(f"Error in direct prediction: {e}")

def test_context_weights():
    """Test context weight functionality"""
    print("\n=== Testing Context Weights ===")
    
    try:
        # Get current weights for student in Gurukul
        weights = agami_predictor.get_context_weights("student_gurukul")
        print("Current weights for student_gurukul:")
        print(json.dumps(weights, indent=2))
        
        # Update weights
        new_weights = {
            "dharma_weight": 1.4,
            "artha_weight": 1.2,
            "kama_weight": 0.7,
            "moksha_weight": 1.3
        }
        
        agami_predictor.update_context_weights("student_gurukul", new_weights)
        print("\nUpdated weights for student_gurukul:")
        print(json.dumps(new_weights, indent=2))
        
        # Verify update
        updated_weights = agami_predictor.get_context_weights("student_gurukul")
        print("\nVerified updated weights:")
        print(json.dumps(updated_weights, indent=2))
        
    except Exception as e:
        print(f"Error in context weights: {e}")

def test_api_endpoints():
    """Test the API endpoints"""
    print("\n=== Testing API Endpoints ===")
    
    try:
        # Test predicting Agami karma
        prediction_data = {
            "user_id": "arjun_123",
            "scenario": {
                "context": {
                    "environment": "gurukul",
                    "role": "student",
                    "goal": "learning"
                }
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/agami/predict",
            json=prediction_data
        )
        
        if response.status_code == 200:
            print("POST /api/v1/agami/predict - SUCCESS")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"POST /api/v1/agami/predict - FAILED: {response.status_code}")
            print(response.text)
            
        # Test getting Agami prediction
        response = requests.get(f"{BASE_URL}/api/v1/agami/user/arjun_123")
        
        if response.status_code == 200:
            print("\nGET /api/v1/agami/user/{{user_id}} - SUCCESS")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"GET /api/v1/agami/user/{{user_id}} - FAILED: {response.status_code}")
            print(response.text)
            
        # Test getting context weights
        response = requests.get(f"{BASE_URL}/api/v1/agami/context-weights/student_gurukul")
        
        if response.status_code == 200:
            print("\nGET /api/v1/agami/context-weights/{{context_key}} - SUCCESS")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"GET /api/v1/agami/context-weights/{{context_key}} - FAILED: {response.status_code}")
            print(response.text)
            
        # Test getting sample scenarios
        response = requests.get(f"{BASE_URL}/api/v1/agami/scenarios")
        
        if response.status_code == 200:
            print("\nGET /api/v1/agami/scenarios - SUCCESS")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"GET /api/v1/agami/scenarios - FAILED: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error testing API endpoints: {e}")

def test_context_weight_api():
    """Test context weight API endpoints"""
    print("\n=== Testing Context Weight API ===")
    
    try:
        # Update context weights via API
        weights_data = {
            "context_key": "warrior_game_realm",
            "weights": {
                "dharma_weight": 1.2,
                "artha_weight": 1.4,
                "kama_weight": 1.3,
                "moksha_weight": 0.8
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/agami/context-weights",
            json=weights_data
        )
        
        if response.status_code == 200:
            print("POST /api/v1/agami/context-weights - SUCCESS")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"POST /api/v1/agami/context-weights - FAILED: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error testing context weight API: {e}")

def cleanup_test_data():
    """Clean up test data"""
    print("\n=== Cleaning up test data ===")
    
    # Remove test users
    user_ids = ["arjun_123", "raju_456"]
    users_col.delete_many({"user_id": {"$in": user_ids}})
    
    print("Test data cleaned up")

def main():
    """Main test function"""
    print("Agami Karma Predictor Test Script")
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
        
        # Test direct prediction
        test_direct_prediction()
        
        # Test context weights
        test_context_weights()
        
        # Test API endpoints
        test_api_endpoints()
        
        # Test context weight API
        test_context_weight_api()
        
        print("\n" + "=" * 50)
        print("Agami Karma Predictor tests completed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        # Clean up test data
        cleanup_test_data()

if __name__ == "__main__":
    main()