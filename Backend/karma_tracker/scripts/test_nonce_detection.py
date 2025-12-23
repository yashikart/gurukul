#!/usr/bin/env python3
"""
Specific test for nonce duplication detection in STP Bridge
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

def test_nonce_duplication_directly():
    """Directly test the nonce duplication detection logic"""
    print("Testing nonce duplication detection directly...")
    
    # Configure the STP bridge with security features enabled
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
    except Exception as e:
        print(f"   ✅ Expected exception caught: {str(e)}")
        if "Duplicate nonce detected" in str(e):
            print("   Nonce duplication detection IS working correctly!")
        else:
            print("   Nonce duplication detection may have an issue!")
    
    print(f"2. Current nonce store size: {len(stp_bridge.nonce_store)}")
    
    # Test with a new nonce
    payload2 = payload.copy()
    payload2["nonce"] = "new-nonce-456"
    payload2["transmission_id"] = "test-456"
    
    print(f"3. Testing with new nonce: {payload2['nonce']}")
    
    try:
        result = stp_bridge._send_with_retry(payload2)
        print(f"   Result: {result.get('status_code', 'No status code')}")
        print("   This is expected since we're not actually connecting to a service")
    except Exception as e:
        print(f"   Exception (expected since service isn't storing response): {str(e)}")

def test_nonce_storage():
    """Test how nonces are stored during normal operation"""
    print("\nTesting nonce storage during normal operation...")
    
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
    
    print(f"Initial nonce store size: {len(stp_bridge.nonce_store)}")
    
    # Create a test signal
    test_signal = {
        "user_id": "test-user-001",
        "action": "completing_lessons",
        "karma_value": 5,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Forward the signal (this should add a nonce to the store)
    try:
        result = stp_bridge.forward_signal(test_signal)
        print(f"Signal forwarding result: {result.get('status')}")
        print(f"Nonce store size after forwarding: {len(stp_bridge.nonce_store)}")
    except Exception as e:
        print(f"Exception during signal forwarding: {str(e)}")
        print(f"Nonce store size after exception: {len(stp_bridge.nonce_store)}")

if __name__ == "__main__":
    test_nonce_duplication_directly()
    test_nonce_storage()