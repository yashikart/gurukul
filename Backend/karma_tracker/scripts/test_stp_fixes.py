#!/usr/bin/env python3
"""
Test script to verify the fixes for nonce duplication detection and health check functionality
"""

import sys
import os
import json
import time
import logging
from datetime import datetime

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Import the STP bridge
from utils.stp_bridge import STPBridge

def test_nonce_duplication_fix():
    """Test that nonce duplication detection works correctly after the fix"""
    print("Testing nonce duplication detection fix...")
    
    # Configure the STP bridge
    config = {
        "insightflow_endpoint": "http://localhost:8001/api/v1/insightflow/receive",
        "retry_attempts": 1,  # Just one attempt for this test
        "timeout": 5,
        "enabled": True,
        "use_mtls": False,
        "signing_method": "hmac-sha256",
        "secret_key": "test-secret-key-for-signing",
        "await_ack": False  # Disable ACK for this test
    }
    
    # Create STP bridge instance
    stp_bridge = STPBridge(config)
    
    # Create a test payload with a specific nonce
    payload = {
        "transmission_id": "test-123",
        "source": "karmachain_feedback_engine",
        "signal": {"test": "data"},
        "timestamp": "2023-01-01T00:00:00Z",
        "nonce": "duplicate-nonce-123"
    }
    
    print(f"1. Testing with fresh nonce: {payload['nonce']}")
    
    # Add the nonce to the store manually to simulate a replay attack
    with stp_bridge.nonce_lock:
        stp_bridge.nonce_store.add(payload["nonce"])
    
    print(f"   Nonce added to store. Current store size: {len(stp_bridge.nonce_store)}")
    
    # Try to send the same nonce - this should raise an exception
    try:
        result = stp_bridge._send_with_retry(payload)
        print(f"   ❌ Unexpected success: {result}")
        print("   This indicates nonce duplication detection is NOT working!")
        return False
    except Exception as e:
        print(f"   ✅ Expected exception caught: {str(e)}")
        if "Duplicate nonce detected" in str(e):
            print("   ✓ Nonce duplication detection IS working correctly!")
            return True
        else:
            print("   Nonce duplication detection may have an issue!")
            return False

def test_nonce_registration_fix():
    """Test that nonces are properly registered before transmission"""
    print("\nTesting nonce registration fix...")
    
    # Configure the STP bridge
    config = {
        "insightflow_endpoint": "http://localhost:8001/api/v1/insightflow/receive",
        "retry_attempts": 1,
        "timeout": 5,
        "enabled": True,
        "use_mtls": False,
        "signing_method": "hmac-sha256",
        "secret_key": "test-secret-key-for-signing",
        "await_ack": False
    }
    
    # Create STP bridge instance
    stp_bridge = STPBridge(config)
    
    # Create a test payload
    payload = {
        "transmission_id": "test-456",
        "source": "karmachain_feedback_engine",
        "signal": {"test": "data"},
        "timestamp": "2023-01-01T00:00:00Z",
        "nonce": "registration-test-nonce-456"
    }
    
    print(f"1. Testing nonce registration for: {payload['nonce']}")
    print(f"   Initial nonce store size: {len(stp_bridge.nonce_store)}")
    
    # Check if nonce is in store before sending (should not be)
    with stp_bridge.nonce_lock:
        before_contains = payload["nonce"] in stp_bridge.nonce_store
    
    print(f"   Nonce in store before sending: {before_contains}")
    
    # Try to send the payload (will fail due to no service, but nonce should be registered)
    try:
        result = stp_bridge._send_with_retry(payload)
        print(f"   Unexpected success: {result}")
    except Exception as e:
        print(f"   Expected exception (no service): {str(e)}")
    
    # Check if nonce is in store after sending attempt
    with stp_bridge.nonce_lock:
        after_contains = payload["nonce"] in stp_bridge.nonce_store
    
    print(f"   Nonce in store after sending attempt: {after_contains}")
    print(f"   Final nonce store size: {len(stp_bridge.nonce_store)}")
    
    if after_contains and not before_contains:
        print("   ✓ Nonce registration IS working correctly!")
        return True
    else:
        print("   ❌ Nonce registration is NOT working correctly!")
        return False

def test_health_check_endpoint_fix():
    """Test that health check uses the correct endpoint"""
    print("\nTesting health check endpoint fix...")
    
    # Configure the STP bridge with explicit health endpoint
    config = {
        "insightflow_endpoint": "http://localhost:8001/api/v1/insightflow/receive",
        "insightflow_health_endpoint": "http://localhost:8001/api/v1/insightflow/health",
        "retry_attempts": 1,
        "timeout": 5,
        "enabled": True,
        "use_mtls": False,
        "signing_method": "hmac-sha256",
        "secret_key": "test-secret-key-for-signing"
    }
    
    # Create STP bridge instance
    stp_bridge = STPBridge(config)
    
    # Call health check
    try:
        result = stp_bridge.health_check()
        print(f"   Health check result: {result.get('status')}")
        print(f"   Health check endpoint: {result.get('endpoint')}")
        
        # Check that the correct endpoint was used
        if result.get('endpoint') == "http://localhost:8001/api/v1/insightflow/health":
            print("   ✓ Health check endpoint IS correct!")
            return True
        else:
            print("   ❌ Health check endpoint is NOT correct!")
            return False
    except Exception as e:
        print(f"   Exception during health check: {str(e)}")
        return False

if __name__ == "__main__":
    print("Running STP Bridge fixes verification tests...\n")
    
    # Run tests
    nonce_test_passed = test_nonce_duplication_fix()
    registration_test_passed = test_nonce_registration_fix()
    health_check_test_passed = test_health_check_endpoint_fix()
    
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    print(f"Nonce duplication detection fix: {'PASS' if nonce_test_passed else 'FAIL'}")
    print(f"Nonce registration fix: {'PASS' if registration_test_passed else 'FAIL'}")
    print(f"Health check endpoint fix: {'PASS' if health_check_test_passed else 'FAIL'}")
    
    all_tests_passed = nonce_test_passed and registration_test_passed and health_check_test_passed
    print(f"\nOverall result: {'ALL TESTS PASSED' if all_tests_passed else 'SOME TESTS FAILED'}")