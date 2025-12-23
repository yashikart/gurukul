"""
Tests for the STP Bridge security enhancements
"""
import unittest
import json
import hashlib
import hmac
from unittest.mock import patch, MagicMock
from utils.stp_bridge import STPBridge


class TestSTPBridgeSecurity(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.config = {
            "insightflow_endpoint": "http://test.example.com/api/v1/insightflow/receive",
            "retry_attempts": 1,
            "timeout": 5,
            "enabled": True,
            "use_mtls": False,
            "signing_method": "hmac-sha256",
            "secret_key": "test-secret-key",
            "await_ack": False
        }
        self.stp_bridge = STPBridge(self.config)
    
    def test_signature_verification(self):
        """Test that payloads are correctly signed using HMAC-SHA256"""
        # Create a test payload
        payload = {
            "transmission_id": "test-123",
            "source": "karmachain_feedback_engine",
            "signal": {"test": "data"},
            "timestamp": "2023-01-01T00:00:00Z",
            "nonce": "nonce-123"
        }
        
        # Generate signature manually
        payload_str = json.dumps(payload, sort_keys=True)
        expected_signature = hmac.new(
            self.config["secret_key"].encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare with bridge-generated signature
        actual_signature = self.stp_bridge._sign_payload(payload)
        self.assertEqual(actual_signature, expected_signature)
    
    def test_nonce_duplication_detection(self):
        """Test that duplicate nonces are detected and rejected"""
        # Create a test payload with a specific nonce
        payload = {
            "transmission_id": "test-123",
            "source": "karmachain_feedback_engine",
            "signal": {"test": "data"},
            "timestamp": "2023-01-01T00:00:00Z",
            "nonce": "duplicate-nonce-123"
        }
        
        # Add the nonce to the store manually to simulate a replay attack
        with self.stp_bridge.nonce_lock:
            self.stp_bridge.nonce_store.add(payload["nonce"])
        
        # Attempt to send the same nonce - should raise an exception
        with self.assertRaises(Exception) as context:
            self.stp_bridge._send_with_retry(payload)
        
        self.assertIn("Duplicate nonce detected", str(context.exception))
    
    @patch('utils.stp_bridge.requests.Session.post')
    def test_ack_timeout_handling(self, mock_post):
        """Test handling of ACK timeouts"""
        # Configure the bridge to await ACKs with a short timeout
        self.stp_bridge.await_ack = True
        self.stp_bridge.ack_timeout = 1  # 1 second timeout
        
        # Mock a successful response from the initial post
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"transmission_id": "test-123"}
        mock_response.content = json.dumps({"transmission_id": "test-123"}).encode()
        mock_post.return_value = mock_response
        
        # Mock the ACK wait to simulate a timeout
        with patch.object(self.stp_bridge, '_wait_for_ack') as mock_wait_for_ack:
            mock_wait_for_ack.return_value = {"status": "nack", "reason": "Timeout"}
            
            # Try to forward a signal - should raise an exception due to NACK
            signal = {"signal_id": "sig-123", "test": "data"}
            result = self.stp_bridge.forward_signal(signal)
            
            # Should return an error status
            self.assertEqual(result["status"], "error")
            self.assertIn("NACK received", result["error"])
    
    def test_bridge_status_tracking(self):
        """Test that bridge status is correctly tracked"""
        # Initially should be active
        self.assertEqual(self.stp_bridge.status, "active")
        
        # Simulate a health check failure
        with patch('utils.stp_bridge.requests.Session.post') as mock_post:
            mock_post.side_effect = Exception("Connection failed")
            health_result = self.stp_bridge.health_check()
            self.assertEqual(health_result["status"], "unhealthy")
            self.assertEqual(self.stp_bridge.status, "offline")
        
        # Simulate a successful health check
        with patch('utils.stp_bridge.requests.Session.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_response.content = b"{}"
            mock_response.elapsed.total_seconds.return_value = 0.1
            mock_post.return_value = mock_response
            
            health_result = self.stp_bridge.health_check()
            self.assertEqual(health_result["status"], "healthy")
            self.assertEqual(self.stp_bridge.status, "active")


if __name__ == '__main__':
    unittest.main()