# Event Payloads Reference

## Request Models

### Log Action Request
**Endpoint**: `/v1/karma/log-action/`

```json
{
  "user_id": "string",
  "action": "string",
  "role": "string",
  "note": "string (optional)",
  "context": "string (optional)",
  "metadata": "object (optional)"
}
```

**Field Descriptions**:
- `user_id`: Unique identifier for the user
- `action`: Action type (must be in valid actions list)
- `role`: Current user role (must be in valid roles list)
- `note`: Optional note or comment about the action
- `context`: Optional context information
- `metadata`: Optional additional metadata object

**Special Notes**:
- Include "auto_appeal" in the note field to automatically create an appeal for Paap-generating actions
- Cheat actions trigger progressive punishment based on user's cheat history

### Appeal Request
**Endpoint**: `/v1/karma/appeal/`

```json
{
  "user_id": "string",
  "action": "string",
  "context": "string (optional)"
}
```

**Field Descriptions**:
- `user_id`: Unique identifier for the user
- `action`: The action being appealed
- `context`: Optional context or reason for the appeal

### Atonement Submission Request
**Endpoint**: `/v1/karma/atonement/submit`

```json
{
  "user_id": "string",
  "plan_id": "string",
  "proof_text": "string"
}
```

**Field Descriptions**:
- `user_id`: Unique identifier for the user
- `plan_id`: The atonement plan ID being submitted
- `proof_text`: Text description of the atonement proof

### Atonement Submission with File Request
**Endpoint**: `/v1/karma/atonement/submit-with-file`

**Multipart Form Data**:
- `user_id`: string
- `plan_id`: string
- `proof_text`: string
- `file`: File upload (optional)

### Death Event Request
**Endpoint**: `/v1/karma/death/event`

```json
{
  "user_id": "string"
}
```

**Field Descriptions**:
- `user_id`: Unique identifier for the user

### Unified Event Request
**Endpoint**: `/v1/karma/event/`

```json
{
  "type": "string",
  "data": "object",
  "timestamp": "string (ISO 8601)",
  "source": "string (optional)",
  "routing_info": "object (optional)"
}
```

**Field Descriptions**:
- `type`: Event type (`life_event`, `atonement`, `appeal`, `death_event`, `stats_request`)
- `data`: Event-specific data object (varies by type)
- `timestamp`: Event timestamp (ISO 8601 format, optional - defaults to current time)
- `source`: Event source identifier (optional)
- `routing_info`: Additional routing information (optional)

**Event Type Data Requirements**:
- **life_event**: Requires `user_id`, `action`, `role` in data object
- **atonement**: Requires `user_id`, `plan_id`, `atonement_type`, `amount` in data object
- **appeal**: Requires `user_id`, `action` in data object
- **death_event**: Requires `user_id` in data object
- **stats_request**: Requires `user_id` in data object

### Unified Event with File Request
**Endpoint**: `/v1/karma/event/with-file`

**Multipart Form Data**:
- `event_type`: string (currently only "atonement_with_file" supported)
- `user_id`: string
- `plan_id`: string
- `atonement_type`: string
- `amount`: number
- `proof_text`: string (optional)
- `tx_hash`: string (optional)
- `proof_file`: File upload (required)

## Response Models

### Log Action Response
```json
{
  "user_id": "string",
  "action": "string",
  "current_role": "string",
  "predicted_next_role": "string",
  "merit_score": "number",
  "reward_token": "string",
  "reward_tier": "string",
  "action_flow": "string",
  "note": "string (optional)",
  "paap_generated": "boolean (optional)",
  "paap_severity": "string (optional)",
  "paap_value": "number (optional)",
  "appeal_created": "boolean (optional)"
}
```

### Appeal Response
```json
{
  "status": "string",
  "message": "string",
  "plan": {
    "plan_id": "string",
    "user_id": "string",
    "action": "string",
    "severity": "string",
    "tasks": [
      {
        "type": "string",
        "description": "string",
        "target_amount": "number",
        "completed_amount": "number",
        "status": "string"
      }
    ],
    "created_at": "string",
    "completed_at": "string (optional)"
  }
}
```

### Atonement Submission Response
```json
{
  "status": "string",
  "message": "string",
  "plan": {
    "plan_id": "string",
    "user_id":string",
    "action": "string",
    "severity": "string",
    "tasks": [
      {
        "type": "string",
        "description": "string",
        "target_amount": "number",
        "completed_amount": "number",
        "status": "string"
      }
    ],
    "created_at": "string",
    "completed_at": "string (optional)"
  }
}
```

### Death Event Response
```json
{
  "status": "string",
  "loka": "string",
  "description": "string",
  "carryover": {
    "net_karma": "number",
    "merit_carryover": "number",
    "role_carryover": "string"
  },
  "paap_tokens_status": {
    "minor": "number",
    "medium": "number",
    "maha": "number",
    "total": "number",
    "status": "string"
  },
  "final_balances": {
    "PunyaTokens": "number",
    "SevaPoints": "number",
    "PaapTokens": "number"
  },
  "merit_score": "number",
  "role": "string",
  "rebirth_count": "number"
}
```

### User Statistics Response
```json
{
  "status": "string",
  "role": "string",
  "merit_score": "number",
  "paap_score": "number",
  "net_karma": "number",
  "balances": {
    "PunyaTokens": "number",
    "SevaPoints": "number",
    "PaapTokens": {
      "minor": "number",
      "medium": "number",
      "maha": "number"
    }
  }
}
```

### Unified Event Response
```json
{
  "status": "string",
  "event_type": "string",
  "message": "string",
  "data": "object",
  "timestamp": "string (ISO 8601)",
  "routing_info": {
    "internal_endpoint": "string",
    "mapped_from": "string"
  }
}
```

**Field Descriptions**:
- `status`: Response status (`success` or `error`)
- `event_type`: Type of event that was processed
- `message`: Human-readable response message
- `data`: Event-specific response data (varies by event type)
- `timestamp`: Response timestamp (ISO 8601 format)
- `routing_info`: Information about internal routing
  - `internal_endpoint`: Internal API endpoint that was called
  - `mapped_from`: Original event type that was mapped

**Event Type Response Data**:
- **life_event**: Returns log action response data
- **atonement**: Returns atonement submission response data
- **appeal**: Returns appeal submission response data
- **death_event**: Returns death event response data
- **stats_request**: Returns user statistics response data
  "action_stats": {
    "total_actions": "number",
    "pending_atonements": "number",
    "completed_atonements": "number"
  },
  "token_attributes": {
    "PunyaTokens": {
      "description": "string",
      "weight": "number",
      "decay_rate": "number"
    },
    "SevaPoints": {
      "description": "string",
      "weight": "number",
      "decay_rate": "number"
    },
    "PaapTokens": {
      "description": "string",
      "weight": "number",
      "decay_rate": "number"
    }
  }
}
```