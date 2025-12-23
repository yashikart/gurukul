#!/usr/bin/env python3
"""
STP Bridge Logging Test Script
Tests the STP bridge security features and generates logs
"""

import sys
import os
import json
import time
import logging
from datetime import datetime

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Now we can import the modules
from utils.stp_bridge import STPBridge
from observability import karmachain_logger, log_security_event

def setup_logging():
    """Setup logging configuration"""
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/stp_bridge_run.log"),
            logging.StreamHandler()
        ]
    )

def test_stp_bridge_security_features():
    """Test all security features of the STP bridge"""
    print("Testing STP Bridge Security Features...")
    
    # Configure the STP bridge with security features enabled
    config = {
        "insightflow_endpoint": "http://localhost:8001/api/v1/insightflow/receive",
        "retry_attempts": 3,
        "timeout": 10,
        "enabled": True,
        "use_mtls": False,  # Set to True if you have certificates
        "cert_file": None,
        "key_file": None,
        "ca_bundle": None,
        "signing_method": "hmac-sha256",
        "secret_key": "test-secret-key-for-signing",
        "await_ack": True,
        "ack_timeout": 30
    }
    
    # Create STP bridge instance
    stp_bridge = STPBridge(config)
    
    # Log initialization
    logging.info("STP Bridge initialized with security features")
    log_security_event(
        request_id="init-001",
        event_type="bridge_initialization",
        description="STP Bridge initialized with security enhancements",
        severity="info"
    )
    
    # Test 1: Signature verification
    print("1. Testing signature verification...")
    try:
        test_signal = {
            "user_id": "test-user-001",
            "action": "completing_lessons",
            "karma_value": 5,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        result = stp_bridge.forward_signal(test_signal)
        logging.info(f"Signal forwarding result: {result}")
        print(f"   ✓ Signal forwarded with status: {result.get('status')}")
        
        if result.get('status') == 'success':
            log_security_event(
                request_id="sig-001",
                event_type="signature_verification",
                description="Signal successfully signed and verified",
                severity="info"
            )
        else:
            log_security_event(
                request_id="sig-001",
                event_type="signature_failure",
                description=f"Signal forwarding failed: {result.get('error')}",
                severity="warning"
            )
            
    except Exception as e:
        logging.error(f"Signature verification test failed: {str(e)}")
        log_security_event(
            request_id="sig-001",
            event_type="signature_error",
            description=f"Error during signature verification: {str(e)}",
            severity="error"
        )
        print(f"   ✗ Signature verification failed: {str(e)}")
    
    # Test 2: Nonce duplication detection (corrected test)
    print("2. Testing nonce duplication detection...")
    try:
        # Create a signal with a fixed timestamp to ensure the same nonce is generated
        fixed_timestamp = "2025-12-04T10:00:00Z"
        test_signal = {
            "user_id": "test-user-002",
            "action": "helping_peers",
            "karma_value": 10,
            "timestamp": fixed_timestamp
        }
        
        # First transmission
        result1 = stp_bridge.forward_signal(test_signal)
        print(f"   First transmission: {result1.get('status')}")
        
        # Second transmission with the same signal (should be blocked by nonce protection)
        result2 = stp_bridge.forward_signal(test_signal)
        print(f"   Second transmission: {result2.get('status')}")
        
        # Check if the second attempt was blocked due to nonce duplication
        if result2.get('status') == 'error' and 'Duplicate nonce' in result2.get('error', ''):
            print("   ✓ Nonce duplication correctly detected")
            log_security_event(
                request_id="nonce-001",
                event_type="replay_protection",
                description="Replay attack prevented by nonce duplication detection",
                severity="info"
            )
        elif result2.get('status') == 'error':
            print(f"   ⚠ Second transmission failed but not due to nonce: {result2.get('error')}")
            log_security_event(
                request_id="nonce-001",
                event_type="replay_protection_uncertain",
                description=f"Second transmission failed: {result2.get('error')}",
                severity="warning"
            )
        else:
            print("   ⚠ Nonce duplication not detected as expected")
            log_security_event(
                request_id="nonce-001",
                event_type="replay_protection_bypass",
                description="Potential replay protection bypass",
                severity="high"
            )
            
    except Exception as e:
        logging.error(f"Nonce duplication test error: {str(e)}")
        log_security_event(
            request_id="nonce-001",
            event_type="replay_protection_error",
            description=f"Error during nonce duplication test: {str(e)}",
            severity="error"
        )
        print(f"   ✗ Nonce duplication test failed: {str(e)}")
    
    # Test 3: Health check
    print("3. Testing health check...")
    try:
        health = stp_bridge.health_check()
        logging.info(f"Health check result: {health}")
        print(f"   Health status: {health.get('status')}")
        
        log_security_event(
            request_id="health-001",
            event_type="bridge_health_check",
            description=f"STP Bridge health check: {health.get('status')}",
            severity="info"
        )
        
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        log_security_event(
            request_id="health-001",
            event_type="bridge_health_error",
            description=f"STP Bridge health check failed: {str(e)}",
            severity="error"
        )
        print(f"   ✗ Health check failed: {str(e)}")
    
    # Test 4: Status tracking
    print("4. Testing status tracking...")
    try:
        status = stp_bridge.status
        logging.info(f"Bridge status: {status}")
        print(f"   Current status: {status}")
        
        # Update metrics
        karmachain_logger.stp_bridge_status = status
        
        log_security_event(
            request_id="status-001",
            event_type="status_tracking",
            description=f"STP Bridge status tracked: {status}",
            severity="info"
        )
        
    except Exception as e:
        logging.error(f"Status tracking failed: {str(e)}")
        print(f"   ✗ Status tracking failed: {str(e)}")
    
    print("\nAll tests completed. Check logs/stp_bridge_run.log for details.")

if __name__ == "__main__":
    setup_logging()
    test_stp_bridge_security_features()