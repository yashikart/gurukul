#!/usr/bin/env python3
"""
Simple STP Bridge Test Script
Tests the STP bridge security features without database dependencies
"""

import sys
import os
import json
import time
import logging
from datetime import datetime

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Import only what we need to avoid database connections
from utils.stp_bridge import STPBridge

def test_nonce_duplication():
    """Test nonce duplication detection directly"""
    print("Testing nonce duplication detection...")
    
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
    
    print(f"1. Testing with nonce: {payload['nonce']}")
    
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

def test_signature_generation():
    """Test signature generation"""
    print("\nTesting signature generation...")
    
    # Configure the STP bridge
    config = {
        "signing_method": "hmac-sha256",
        "secret_key": "test-secret-key-for-signing"
    }
    
    # Create STP bridge instance
    stp_bridge = STPBridge(config)
    
    # Create a test payload
    payload = {
        "transmission_id": "test-456",
        "source": "karmachain_feedback_engine",
        "signal": {"test": "data"},
        "timestamp": "2023-01-01T00:00:00Z",
        "nonce": "nonce-456"
    }
    
    try:
        signature = stp_bridge._sign_payload(payload)
        print(f"   Generated signature: {signature[:32]}...")
        print("   ✓ Signature generation is working!")
        return True
    except Exception as e:
        print(f"   ❌ Signature generation failed: {str(e)}")
        return False

def test_status_tracking():
    """Test status tracking"""
    print("\nTesting status tracking...")
    
    # Create STP bridge instance
    stp_bridge = STPBridge()
    
    # Check initial status
    initial_status = stp_bridge.status
    print(f"   Initial status: {initial_status}")
    
    # Change status
    stp_bridge.status = "degraded"
    updated_status = stp_bridge.status
    print(f"   Updated status: {updated_status}")
    
    if updated_status == "degraded":
        print("   ✓ Status tracking is working!")
        return True
    else:
        print("   ❌ Status tracking is not working!")
        return False

if __name__ == "__main__":
    print("Running simple STP Bridge tests...\n")
    
    # Run tests
    nonce_test_passed = test_nonce_duplication()
    signature_test_passed = test_signature_generation()
    status_test_passed = test_status_tracking()
    
    print("\n" + "="*50)
    print("TEST RESULTS SUMMARY")
    print("="*50)
    print(f"Nonce duplication detection: {'PASS' if nonce_test_passed else 'FAIL'}")
    print(f"Signature generation: {'PASS' if signature_test_passed else 'FAIL'}")
    print(f"Status tracking: {'PASS' if status_test_passed else 'FAIL'}")
    
    all_tests_passed = nonce_test_passed and signature_test_passed and status_test_passed
    print(f"\nOverall result: {'ALL TESTS PASSED' if all_tests_passed else 'SOME TESTS FAILED'}")