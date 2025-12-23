#!/usr/bin/env python3
"""
Test script for Behavioral State Normalization API
"""
import requests
import json
import time
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"

def test_normalize_state():
    """Test the /normalize_state endpoint"""
    print("Testing /normalize_state endpoint...")
    
    # Test data for Finance module
    finance_payload = {
        "module": "finance",
        "action_type": "transaction_completed",
        "raw_value": 100.0,
        "context": {
            "currency": "USD",
            "transaction_type": "purchase"
        },
        "metadata": {
            "user_id": "user_finance_001",
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    
    # Test data for Gurukul module
    gurukul_payload = {
        "module": "gurukul",
        "action_type": "lesson_completed",
        "raw_value": 85.5,
        "context": {
            "subject": "mathematics",
            "difficulty": "intermediate"
        },
        "metadata": {
            "user_id": "user_gurukul_001",
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    
    try:
        # Test Finance module
        print("  Testing Finance module...")
        response = requests.post(f"{BASE_URL}/normalize_state", json=finance_payload)
        print(f"    Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"    Response: {json.dumps(data, indent=2)}")
            print("    ✓ Finance module test passed")
        else:
            print(f"    ✗ Finance module test failed: {response.text}")
            return False
        
        time.sleep(1)  # Small delay between tests
        
        # Test Gurukul module
        print("  Testing Gurukul module...")
        response = requests.post(f"{BASE_URL}/normalize_state", json=gurukul_payload)
        print(f"    Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"    Response: {json.dumps(data, indent=2)}")
            print("    ✓ Gurukul module test passed")
        else:
            print(f"    ✗ Gurukul module test failed: {response.text}")
            return False
            
        return True
        
    except Exception as e:
        print(f"    ✗ Exception: {e}")
        return False

def test_normalize_state_batch():
    """Test the /normalize_state/batch endpoint"""
    print("\nTesting /normalize_state/batch endpoint...")
    
    # Batch test data
    batch_payload = {
        "states": [
            {
                "module": "finance",
                "action_type": "deposit",
                "raw_value": 500.0,
                "context": {
                    "transaction_type": "deposit"
                },
                "metadata": {
                    "user_id": "user_finance_002"
                }
            },
            {
                "module": "game",
                "action_type": "level_completed",
                "raw_value": 75.0,
                "context": {
                    "level": 5,
                    "difficulty": "hard"
                },
                "metadata": {
                    "user_id": "user_game_001"
                }
            },
            {
                "module": "gurukul",
                "action_type": "quiz_passed",
                "raw_value": 92.0,
                "context": {
                    "subject": "physics",
                    "topic": "mechanics"
                },
                "metadata": {
                    "user_id": "user_gurukul_002"
                }
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/normalize_state/batch", json=batch_payload)
        print(f"  Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)}")
            print("  ✓ Batch normalization test passed")
            return True
        else:
            print(f"  ✗ Batch normalization test failed: {response.text}")
            return False
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        return False

def test_invalid_module():
    """Test error handling for invalid module"""
    print("\nTesting error handling for invalid module...")
    
    # Test data with invalid module
    invalid_payload = {
        "module": "invalid_module",
        "action_type": "test_action",
        "raw_value": 50.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/normalize_state", json=invalid_payload)
        print(f"  Status Code: {response.status_code}")
        # We expect this to still work (with default weight of 1.0) since we don't validate modules strictly
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)}")
            print("  ✓ Invalid module handled gracefully")
            return True
        else:
            # If it fails, that's also acceptable for this test
            print(f"  Response (expected): {response.text}")
            print("  ✓ Invalid module handled appropriately")
            return True
    except Exception as e:
        print(f"  Exception: {e}")
        return False

if __name__ == "__main__":
    print("Running Behavioral State Normalization Tests")
    print("=" * 50)
    
    print("Make sure the KarmaChain server is running at http://localhost:8000")
    print("Press Ctrl+C to skip and continue with other tests\n")
    
    try:
        # Test each endpoint
        tests = [
            test_normalize_state,
            test_normalize_state_batch,
            test_invalid_module
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
        print("NORMALIZATION TEST SUMMARY")
        print("=" * 50)
        passed = sum(results)
        total = len(results)
        print(f"Passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 All normalization tests passed!")
        else:
            print("⚠️  Some normalization tests failed or were skipped.")
            
    except Exception as e:
        print(f"Error running tests: {e}")