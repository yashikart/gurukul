# Behavioral State Normalization

## Overview

The Behavioral State Normalization feature unifies multi-module behavioral inputs into a standardized karmic signal schema. This allows different departments (Finance, Game, Gurukul, Insight) to contribute to the overall karma calculation using a consistent framework.

## Schema

The normalized state follows this schema (defined in `schemas/state_schema.json`):

```json
{
  "state_id": "uuid",
  "module": "finance | game | gurukul | insight",
  "action_type": "string",
  "weight": "float",
  "feedback_value": "float",
  "timestamp": "iso8601"
}
```

## API Endpoints

### Normalize Single State
```
POST /api/v1/normalize_state
```

**Request Body:**
```json
{
  "module": "string",
  "action_type": "string",
  "raw_value": "float",
  "context": "object (optional)",
  "metadata": "object (optional)"
}
```

**Response:**
```json
{
  "state_id": "string",
  "module": "string",
  "action_type": "string",
  "weight": "float",
  "feedback_value": "float",
  "timestamp": "string"
}
```

### Normalize Batch States
```
POST /api/v1/normalize_state/batch
```

**Request Body:**
```json
{
  "states": [
    {
      "module": "string",
      "action_type": "string",
      "raw_value": "float",
      "context": "object (optional)",
      "metadata": "object (optional)"
    }
  ]
}
```

**Response:**
```json
[
  {
    "state_id": "string",
    "module": "string",
    "action_type": "string",
    "weight": "float",
    "feedback_value": "float",
    "timestamp": "string"
  }
]
```

## Module Weights

Each module has a default weight defined in `context_weights.json`:

- **Finance**: 1.0
- **Game**: 1.2
- **Gurukul**: 1.3
- **Insight**: 1.1

The normalized feedback value is calculated as: `feedback_value = raw_value * weight`

## Integration Example

### Finance Module Integration
```python
import requests

# Send a transaction completion event
payload = {
    "module": "finance",
    "action_type": "transaction_completed",
    "raw_value": 100.0,
    "context": {
        "currency": "USD",
        "transaction_type": "purchase"
    },
    "metadata": {
        "user_id": "user_finance_001"
    }
}

response = requests.post("http://localhost:8000/api/v1/normalize_state", json=payload)
normalized_state = response.json()
```

### Gurukul Module Integration
```python
import requests

# Send a lesson completion event
payload = {
    "module": "gurukul",
    "action_type": "lesson_completed",
    "raw_value": 85.5,
    "context": {
        "subject": "mathematics",
        "difficulty": "intermediate"
    },
    "metadata": {
        "user_id": "user_gurukul_001"
    }
}

response = requests.post("http://localhost:8000/api/v1/normalize_state", json=payload)
normalized_state = response.json()
```

## Testing

Run the normalization tests:
```bash
python tests/test_normalization.py
```

Run the integration demo:
```bash
python scripts/finance_gurukul_stubs.py
```

## Logging

All normalized states are automatically logged to the Karma Ledger (karma_events collection in MongoDB) for audit and analysis purposes.