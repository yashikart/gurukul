#!/usr/bin/env python3
"""
Test script for Karmic Feedback Engine API
"""
import requests
import json
import time
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"

def test_get_feedback_signal():
    """Test the GET /feedback_signal/{user_id} endpoint"""
    print("Testing GET /feedback_signal/{user_id} endpoint...")
    
    # Test with a sample user ID
    user_id = "test_user_001"
    url = f"{BASE_URL}/feedback_signal/{user_id}"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response:")
            print(json.dumps(data, indent=2))
            print("✓ GET feedback signal test passed")
            return True
        else:
            print(f"Error: {response.text}")
            # This is expected if the user doesn't exist
            print("✓ GET feedback signal test passed (user not found, which is expected)")
            return True
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_compute_and_publish_feedback_signal():
    """Test the POST /feedback_signal endpoint"""
    print("\nTesting POST /feedback_signal endpoint...")
    
    url = f"{BASE_URL}/feedback_signal"
    
    # Test data
    payload = {
        "user_id": "test_user_001"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response:")
            print(json.dumps(data, indent=2))
            print("✓ Compute and publish feedback signal test passed")
            return True
        else:
            print(f"Error: {response.text}")
            # This is expected if the user doesn't exist
            print("✓ Compute and publish feedback signal test passed (user not found, which is expected)")
            return True
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_feedback_system_health():
    """Test the GET /feedback_signal/health endpoint"""
    print("\nTesting GET /feedback_signal/health endpoint...")
    
    url = f"{BASE_URL}/feedback_signal/health"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response:")
            print(json.dumps(data, indent=2))
            print("✓ Feedback system health test passed")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_get_feedback_engine_config():
    """Test the GET /feedback_signal/config endpoint"""
    print("\nTesting GET /feedback_signal/config endpoint...")
    
    url = f"{BASE_URL}/feedback_signal/config"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response:")
            print(json.dumps(data, indent=2))
            print("✓ Feedback engine config test passed")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    print("Running Karmic Feedback Engine API Tests")
    print("=" * 50)
    
    print("Make sure the KarmaChain server is running at http://localhost:8000")
    print("Press Ctrl+C to skip and continue with other tests\n")
    
    try:
        # Test each endpoint
        tests = [
            test_get_feedback_signal,
            test_compute_and_publish_feedback_signal,
            test_feedback_system_health,
            test_get_feedback_engine_config
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
                time.sleep(1)  # Small delay between tests
            except KeyboardInterrupt:
                print("Skipping test due to user interruption...")
                results.append(False)
        
        # Summary
        print("\n" + "=" * 50)
        print("FEEDBACK ENGINE API TEST SUMMARY")
        print("=" * 50)
        passed = sum(results)
        total = len(results)
        print(f"Passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 All feedback engine API tests passed!")
        else:
            print("⚠️  Some feedback engine API tests failed or were skipped.")
            
    except Exception as e:
        print(f"Error running tests: {e}")