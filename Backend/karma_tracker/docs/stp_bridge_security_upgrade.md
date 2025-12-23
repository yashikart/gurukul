# STP Bridge Security Upgrade Documentation

## Overview

This document describes the security enhancements made to the STP (Signal Transmission Protocol) Bridge in the KarmaChain system. The upgrade transforms the basic STP bridge into a fully compliant SSPL Phase III secure bridge with mutual TLS support, message signing, replay protection, and ACK/NACK protocols.

## Security Features Implemented

### 1. Mutual TLS Handshake Support

The STP bridge now supports mutual TLS (mTLS) authentication for secure communication with InsightFlow:

- Configuration options for certificate files (cert_file, key_file)
- CA bundle verification support (ca_bundle)
- Session reuse for improved performance
- Automatic certificate loading and validation

Configuration example:
```python
config = {
    "use_mtls": True,
    "cert_file": "/path/to/client.crt",
    "key_file": "/path/to/client.key",
    "ca_bundle": "/path/to/ca-bundle.crt"
}
```

### 2. Message Signing

Two message signing methods are supported:

#### HMAC-SHA256 (Default)
- Cryptographically secure message authentication
- Shared secret key configuration
- Automatic signature generation for all outbound messages

#### Ed25519 (Planned)
- Asymmetric signature support
- Public/private key pair authentication
- Future enhancement placeholder implemented

### 3. Nonce-Based Replay Protection

Protection against replay attacks through:

- Unique nonce generation for each message
- In-memory nonce storage with thread-safe access
- Duplicate detection and rejection
- Automatic cleanup of old nonces to prevent memory leaks

### 4. ACK/NACK Protocol

Reliable message delivery through:

- Configurable ACK waiting (await_ack setting)
- Timeout handling (ack_timeout setting)
- Automatic retry logic for failed transmissions
- Explicit NACK handling with error reporting

## API Changes

### New Configuration Options

The STPBridge constructor now accepts additional security configuration parameters:

```python
STPBridge(config={
    # Existing options
    "insightflow_endpoint": "http://localhost:8001/api/v1/insightflow/receive",
    "retry_attempts": 3,
    "timeout": 10,
    "enabled": True,
    
    # New security options
    "use_mtls": False,
    "cert_file": None,
    "key_file": None,
    "ca_bundle": None,
    "signing_method": "hmac-sha256",
    "secret_key": "default-secret-key",
    "await_ack": True,
    "ack_timeout": 30
})
```

### Enhanced Methods

All outbound message methods now include security features automatically:
- `forward_signal()`
- `batch_forward_signals()`
- `health_check()`

## Observability

The STP bridge status is now integrated into the system metrics:

- Status values: "active" | "degraded" | "offline"
- Automatic status updates based on health checks
- Integration with the observability system
- Metrics endpoint includes `stp_bridge_status` field

## Testing

A comprehensive test suite has been added in `tests/test_stp_bridge.py`:

1. **Signature Verification Test** - Validates HMAC-SHA256 signature generation
2. **Nonce Duplication Test** - Ensures replay protection works correctly
3. **ACK Timeout Test** - Tests ACK/NACK protocol handling

Run tests with:
```bash
python -m pytest tests/test_stp_bridge.py -v
```

## Security Considerations

1. **Secret Management**: Ensure secret keys are properly secured and not hardcoded
2. **Certificate Storage**: Protect certificate files with appropriate file permissions
3. **Network Security**: Use secure network connections between services
4. **Monitoring**: Regularly monitor STP bridge status and error logs

## Backward Compatibility

The security enhancements are backward compatible. Existing configurations will continue to work with default security settings. To enable security features, simply add the new configuration options.

## Example Usage

```python
from utils.stp_bridge import STPBridge

# Secure configuration
secure_config = {
    "insightflow_endpoint": "https://insightflow.example.com/api/v1/receive",
    "use_mtls": True,
    "cert_file": "/etc/ssl/certs/karmachain-client.crt",
    "key_file": "/etc/ssl/private/karmachain-client.key",
    "ca_bundle": "/etc/ssl/certs/ca-bundle.crt",
    "signing_method": "hmac-sha256",
    "secret_key": "super-secret-key-change-me",
    "await_ack": True,
    "ack_timeout": 30
}

secure_bridge = STPBridge(secure_config)
result = secure_bridge.forward_signal({"user_id": "user123", "action": "test_action"})
```