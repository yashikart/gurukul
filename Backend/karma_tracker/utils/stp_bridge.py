"""
STP Bridge Module

Configurable bridge to forward karmic feedback signals to InsightFlow.
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests
from fastapi import HTTPException
import hashlib
import hmac
import time
import ssl
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519
from cryptography.hazmat.primitives.serialization import load_pem_private_key
import threading

# Setup logging
logger = logging.getLogger(__name__)

class STPBridge:
    """STP (Signal Transmission Protocol) Bridge for forwarding signals to InsightFlow"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the STP bridge"""
        self.config = config or {}
        self.insightflow_endpoint = self.config.get(
            "insightflow_endpoint", 
            "http://localhost:8001/api/v1/insightflow/receive"
        )
        self.insightflow_health_endpoint = self.config.get(
            "insightflow_health_endpoint", 
            "http://localhost:8001/api/v1/insightflow/health"
        )
        self.retry_attempts = self.config.get("retry_attempts", 3)
        self.timeout = self.config.get("timeout", 10)
        self.enabled = self.config.get("enabled", True)
        
        # Security configuration
        self.use_mtls = self.config.get("use_mtls", False)
        self.cert_file = self.config.get("cert_file")
        self.key_file = self.config.get("key_file")
        self.ca_bundle = self.config.get("ca_bundle")
        
        # Signing configuration
        self.signing_method = self.config.get("signing_method", "hmac-sha256")
        self.secret_key = self.config.get("secret_key", "default-secret-key")
        
        # Replay protection
        self.nonce_store = set()
        self.nonce_lock = threading.Lock()
        self.nonce_cleanup_interval = self.config.get("nonce_cleanup_interval", 3600)  # 1 hour
        self.last_nonce_cleanup = time.time()
        
        # ACK/NACK configuration
        self.await_ack = self.config.get("await_ack", True)
        self.ack_timeout = self.config.get("ack_timeout", 30)
        
        # Status tracking
        self.status = "active"
        
        # Session for connection reuse
        self.session = requests.Session()
        if self.use_mtls and self.cert_file and self.key_file:
            self.session.cert = (self.cert_file, self.key_file)
            if self.ca_bundle:
                self.session.verify = self.ca_bundle
        
    def forward_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Forward karmic feedback signal to InsightFlow
        
        Args:
            signal: Karmic feedback signal to forward
            
        Returns:
            Dict with forwarding result
        """
        if not self.enabled:
            return {
                "status": "skipped",
                "message": "STP bridge is disabled",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        signal_id = signal.get("signal_id", str(uuid.uuid4()))
        
        try:
            # Clean up old nonces periodically
            self._cleanup_nonces()
            
            # Prepare the payload for InsightFlow
            payload = {
                "transmission_id": str(uuid.uuid4()),
                "source": "karmachain_feedback_engine",
                "signal": signal,
                "timestamp": datetime.utcnow().isoformat(),
                "nonce": str(uuid.uuid4())  # For replay protection
            }
            
            # Add signature
            payload["signature"] = self._sign_payload(payload)
            
            # Send to InsightFlow with retry logic
            response = self._send_with_retry(payload)
            
            # Handle ACK/NACK if required
            if self.await_ack:
                ack_result = self._wait_for_ack(response.get("transmission_id"))
                if ack_result.get("status") == "nack":
                    raise Exception(f"NACK received: {ack_result.get('reason', 'Unknown reason')}")
            
            # Log successful transmission
            logger.info(f"Signal {signal_id} forwarded to InsightFlow successfully")
            
            return {
                "status": "success",
                "signal_id": signal_id,
                "transmission_id": payload["transmission_id"],
                "response": response,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error forwarding signal {signal_id} to InsightFlow: {str(e)}"
            logger.error(error_msg)
            self.status = "degraded"
            
            return {
                "status": "error",
                "signal_id": signal_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _send_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send payload with retry logic
        
        Args:
            payload: Payload to send
            
        Returns:
            Dict with response details
        """
        last_exception = Exception("Unknown error")
        
        for attempt in range(self.retry_attempts):
            try:
                # Check for replay before sending
                if "nonce" in payload:
                    with self.nonce_lock:
                        if payload["nonce"] in self.nonce_store:
                            raise Exception("Duplicate nonce detected - possible replay attack")
                        # Pre-register the nonce to prevent race conditions
                        self.nonce_store.add(payload["nonce"])
                
                response = self.session.post(
                    self.insightflow_endpoint,
                    json=payload,
                    timeout=self.timeout
                )
                
                response_data = response.json() if response.content else {}
                
                if response.status_code in [200, 201]:
                    return {
                        "status_code": response.status_code,
                        "response": response_data,
                        "attempt": attempt + 1
                    }
                else:
                    # Only remove the nonce from store if it's a permanent error
                    # For temporary errors, we want to keep the nonce to prevent replays
                    if response.status_code not in [429, 500, 502, 503, 504]:  # Don't remove for temporary errors
                        if "nonce" in payload:
                            with self.nonce_lock:
                                self.nonce_store.discard(payload["nonce"])
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed with status {response.status_code}"
                    )
                    last_exception = HTTPException(
                        status_code=response.status_code,
                        detail=f"InsightFlow returned status {response.status_code}"
                    )
                    
            except Exception as e:
                # For connection errors, keep the nonce in store to prevent replays
                # Only remove for definitive errors
                is_connection_error = "Max retries exceeded" in str(e) or "Connection refused" in str(e)
                if not is_connection_error:
                    if "nonce" in payload:
                        with self.nonce_lock:
                            self.nonce_store.discard(payload["nonce"])
                        
                logger.warning(f"Attempt {attempt + 1} failed with exception: {str(e)}")
                last_exception = e
        
        # If we get here, all attempts failed
        self.status = "degraded"
        raise last_exception
    
    def batch_forward_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Forward multiple signals in batch
        
        Args:
            signals: List of signals to forward
            
        Returns:
            List of forwarding results
        """
        results = []
        
        for signal in signals:
            result = self.forward_signal(signal)
            results.append(result)
            
        return results
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the STP bridge connection
        
        Returns:
            Dict with health status
        """
        try:
            # Send a simple health check ping to the correct endpoint
            health_payload = {
                "transmission_id": str(uuid.uuid4()),
                "source": "karmachain_feedback_engine",
                "type": "health_check",
                "timestamp": datetime.utcnow().isoformat(),
                "nonce": str(uuid.uuid4())
            }
            
            # Add signature
            health_payload["signature"] = self._sign_payload(health_payload)
            
            response = self.session.post(
                self.insightflow_health_endpoint,  # Use the correct health endpoint
                json=health_payload,
                timeout=self.timeout
            )
            
            # Update status based on health check result
            if response.status_code in [200, 201]:
                self.status = "active"
                status = "healthy"
            else:
                self.status = "degraded"
                status = "unhealthy"
            
            return {
                "status": status,
                "endpoint": self.insightflow_health_endpoint,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.status = "offline"
            return {
                "status": "unhealthy",
                "endpoint": self.insightflow_health_endpoint,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _sign_payload(self, payload: Dict[str, Any]) -> str:
        """
        Sign payload using configured method
        
        Args:
            payload: Payload to sign
            
        Returns:
            Signature string
        """
        payload_str = json.dumps(payload, sort_keys=True)
        
        if self.signing_method == "hmac-sha256":
            return hmac.new(
                self.secret_key.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
        elif self.signing_method == "ed25519":
            # For Ed25519, we would need a private key
            # This is a placeholder implementation
            return f"ed25519_signature_placeholder_{hashlib.sha256(payload_str.encode()).hexdigest()}"
        else:
            raise ValueError(f"Unsupported signing method: {self.signing_method}")
    
    def _cleanup_nonces(self):
        """
        Clean up old nonces periodically to prevent memory leaks
        """
        # Simple implementation - in a production system, you might want
        # to use a more sophisticated approach with timestamps
        if time.time() - self.last_nonce_cleanup > self.nonce_cleanup_interval:
            with self.nonce_lock:
                # Keep only the most recent 10000 nonces
                if len(self.nonce_store) > 10000:
                    # Convert to list, sort, and keep the last 10000
                    nonce_list = list(self.nonce_store)
                    self.nonce_store = set(nonce_list[-10000:])
            self.last_nonce_cleanup = time.time()
    
    def _wait_for_ack(self, transmission_id: str) -> Dict[str, Any]:
        """
        Wait for ACK/NACK for a transmission (placeholder implementation)
        In a real system, this would listen for a response from InsightFlow
        
        Args:
            transmission_id: ID of transmission to wait for
            
        Returns:
            Dict with ACK/NACK result
        """
        # Placeholder implementation - in a real system, this would
        # implement a proper ACK/NACK protocol
        return {"status": "ack", "transmission_id": transmission_id}

# Global instance
stp_bridge = STPBridge()

# Convenience functions
def forward_karmic_signal(signal: Dict[str, Any]) -> Dict[str, Any]:
    """Forward a karmic signal to InsightFlow"""
    return stp_bridge.forward_signal(signal)

def batch_forward_karmic_signals(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Forward multiple karmic signals to InsightFlow"""
    return stp_bridge.batch_forward_signals(signals)

def check_stp_bridge_health() -> Dict[str, Any]:
    """Check the health of the STP bridge"""
    return stp_bridge.health_check()