# Unified Event API Documentation

## Overview

The `/v1/karma/event/` endpoint provides a unified gateway for all karmic actions, allowing other departments to trigger karmic events through a single standard interface.

## Endpoint

**POST** `/v1/karma/event/`

## Request Format

```json
{
  "type": "life_event",
  "data": {
    // Event-specific data payload
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "source": "game_engine"
}
```

### Request Fields

- `type` (string, required): Event type identifier
- `data` (object, required): Event-specific data payload
- `timestamp` (string, optional): Event timestamp (defaults to current time)
- `source` (string, optional): Source system or department

## Supported Event Types

### 1. `life_event`
Maps to the log-action endpoint for logging user actions.

**Required data fields:**
- `user_id` (string)
- `action` (string)
- `role` (string)

**Optional data fields:**
- `note` (string)
- `context` (string)
- `metadata` (object)

**Example:**
```json
{
  "type": "death_event",
  "data": {
    "user_id": "player123",
    "action": "cheat",
    "note": "Donated to charity"
  }
}
```

### 2. `atonement`
Maps to the atonement submission endpoint.

**Required data fields:**
- `user_id` (string)
- `plan_id` (string)
- `atonement_type` (string)
- `amount` (number)

**Optional data fields:**
- `proof_text` (string)
- `tx_hash` (string)

**Example:**
```json
{
  "type": "atonement",
  "data": {
    "user_id": "player123",
    "plan_id": "player123_cheat_0",
    "atonement_type": "Jap",
    "amount": 100,
    "proof_text": "Donated to local temple"
  }
}
```

### 3. `appeal`
Maps to the appeal endpoint for karma appeals.

**Required data fields:**
- `user_id` (string)
- `action` (string)

**Optional data fields:**
- `context` (string)

**Example:**
```json
{
  "type": "appeal",
  "data": {
    "user_id": "player123",
    "action": "theft",
    "context": "Was forced by circumstances"
  }
}
```

### 4. `death_event`
Maps to the death event endpoint.

**Required data fields:**
- `user_id` (string)

**Example:**
```json
{
  "type": "death_event",
  "data": {
    "user_id": "player123"
  }
}
```

### 5. `stats_request`
Maps to the user statistics endpoint.

**Required data fields:**
- `user_id` (string)

**Example:**
```json
{
  "type": "stats_request",
  "data": {
    "user_id": "player123"
  }
}
```

## Response Format

```json
{
  "status": "success",
  "event_type": "life_event",
  "message": "Life event logged successfully",
  "data": {
    // Response data from internal endpoint
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "routing_info": {
    "internal_endpoint": "/v1/karma/log-action/",
    "mapped_from": "life_event"
  }
}
```

## File Upload Support

For atonement submissions with file uploads, use the dedicated endpoint:

**POST** `/v1/karma/event/with-file`

**Form Data:**
- `event_type`: "atonement_with_file"
- `user_id`: User ID
- `plan_id`: Atonement plan ID
- `atonement_type`: Type of atonement
- `amount`: Amount/value
- `proof_text`: Text proof (optional)
- `tx_hash`: Transaction hash (optional)
- `proof_file`: File upload (optional, max 1MB)

## Example for event/with_file
{
  "event_type": "atonement_with_file
  "user_id": "player123",
  "plan_id": "player123_cheat_0"
  "atonement_type": "Jap"
  "amount": "100"
  "proof_text": "Donate to Local Charity"
  "tx_hash": "68e77990e1297f2469f1fcde"
  "proof_file": "Donate_atonement.jpg"
}

## Important Noticed for atonement_with_file
while uploading atonement_with_file if the proof_text is Donation then file name should be also start with donation_atonement or otherwise it will show error this goes for only Unified Events recheck and upload the file with proper name.

## Error Handling

The unified endpoint returns standard HTTP status codes:

- `200`: Success
- `400`: Bad request (invalid event type or missing required fields)
- `404`: Resource not found
- `500`: Internal server error

## Usage Examples

### Python Example
```python
import requests
import json

# Log a life event
payload = {
    "type": "life_event",
    "data": {
        "user_id": "player123",
        "action": "help_others",
        "role": "priest"
    },
    "source": "game_engine"
}

response = requests.post(
    "http://localhost:8000/v1/karma/event/",
    json=payload
)

print(response.json())
```

### cURL Example
```bash
curl -X POST http://localhost:8000/v1/karma/event/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "death_event",
    "data": {"user_id": "player123"},
    "source": "game_engine"
  }'
```

## Benefits

1. **Single Entry Point**: One endpoint for all karmic actions
2. **Standard Interface**: Consistent request/response format across all event types
3. **Department Integration**: Easy integration for other departments and systems
4. **Future Extensibility**: New event types can be added without changing the interface
5. **Routing Transparency**: Response includes information about which internal endpoint was used

## Integration Notes

- The unified endpoint acts as a router to internal endpoints
- All existing validation and business logic is preserved
- File uploads require the dedicated `/with-file` endpoint
- Event types are case-sensitive
- Timestamps should be in ISO 8601 format