# Karma Tracker API Endpoints

## Overview

The Karma Tracker provides secure API endpoints for accessing karma profiles, logging user actions, and submitting atonement completions. These endpoints are designed for cross-module integration with Finance, InsightFlow, Gurukul, and Game modules.

## Endpoints

### GET /api/v1/karma/{user_id}

Retrieve the complete karma profile for a user.

**Response Format:**
```json
{
  "user_id": "string",
  "role": "string",
  "merit_score": "number",
  "paap_score": "number",
  "net_karma": "number",
  "weighted_karma_score": "number",
  "balances": {
    "DharmaPoints": "number",
    "SevaPoints": "number",
    "PunyaTokens": "number",
    "PaapTokens": {
      "minor": "number",
      "medium": "number",
      "maha": "number"
    },
    // ... other karma types
  },
  "action_stats": {
    "total_actions": "number",
    "pending_atonements": "number",
    "completed_atonements": "number"
  },
  "corrective_guidance": [
    {
      "practice": "string",
      "reason": "string",
      "urgency": "string",
      "weight": "number"
    }
  ],
  "module_scores": {
    "finance": "number",
    "insightflow": "number",
    "gurukul": "number",
    "game": "number"
  },
  "last_updated": "datetime"
}
```

### POST /api/v1/log-action/

Log a user action and update their karma.

**Request Format:**
```json
{
  "user_id": "string",
  "action": "string",
  "role": "string (optional, default: learner)",
  "intensity": "number (optional, default: 1.0)",
  "context": "string (optional)",
  "metadata": "object (optional)"
}
```

**Response Format:**
```json
{
  "user_id": "string",
  "action": "string",
  "current_role": "string",
  "predicted_next_role": "string",
  "merit_score": "number",
  "karma_impact": "number",
  "reward_token": "string",
  "reward_value": "number",
  "paap_generated": "boolean",
  "paap_severity": "string",
  "paap_value": "number",
  "corrective_recommendations": [
    {
      "practice": "string",
      "reason": "string",
      "urgency": "string",
      "weight": "number"
    }
  ],
  "module_impacts": {
    "finance": "number",
    "insightflow": "number",
    "gurukul": "number",
    "game": "number"
  },
  "transaction_id": "string"
}
```

### POST /api/v1/submit-atonement/

Validate atonement completion and reduce PaapTokens.

**Request Format:**
```json
{
  "user_id": "string",
  "plan_id": "string",
  "atonement_type": "string",
  "amount": "number",
  "proof_text": "string (optional)",
  "tx_hash": "string (optional)"
}
```

**Response Format:**
```json
{
  "status": "string",
  "message": "string",
  "user_id": "string",
  "plan_id": "string",
  "karma_adjustment": "number",
  "paap_reduction": "number",
  "new_role": "string",
  "module_impacts": {
    "finance": "number",
    "insightflow": "number",
    "gurukul": "number",
    "game": "number"
  },
  "transaction_id": "string"
}
```

## Module Integration

The Karma Tracker returns scores for four core modules:

1. **Finance**: Based on PunyaTokens and SevaPoints, representing ethical wealth generation
2. **InsightFlow**: Based on DharmaPoints, representing learning and wisdom acquisition
3. **Gurukul**: Based on SevaPoints and DharmaPoints, representing teaching and mentoring capabilities
4. **Game**: Based on overall engagement metrics, representing user participation and growth

## Logging and Metadata

All API calls are logged with:
- Unique event IDs
- Timestamps
- Source module information
- Processing status (processing, completed, failed)
- Error messages for failed requests
- Response data for successful requests

This metadata enables future cross-module propagation and system analytics.