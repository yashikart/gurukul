# Rnanubandhan API Documentation

## Overview

The Rnanubandhan API provides endpoints for managing karmic debt relationships between users. Rnanubandhan (karmic debt) represents the invisible bonds that connect individuals through their actions, creating a network of mutual obligations and influences.

## Base URL

```
http://localhost:8000/api/v1/rnanubandhan
```

## Endpoints

### Get User's Rnanubandhan Network

**GET** `/api/v1/rnanubandhan/{user_id}`

Get a complete summary of a user's Rnanubandhan network including debts (what they owe) and credits (what others owe them).

#### Parameters
- `user_id` (path): The ID of the user

#### Response
```json
{
  "status": "success",
  "user_id": "user123",
  "network_summary": {
    "user_id": "user123",
    "total_debt": 50.0,
    "total_credit": 30.0,
    "net_position": -20.0,
    "active_debts": 3,
    "active_credits": 2,
    "unique_debtors": ["user456", "user789"],
    "unique_creditors": ["user111", "user222", "user333"],
    "relationship_count": 5
  },
  "debts": [
    {
      "_id": "rel_123",
      "debtor_id": "user123",
      "receiver_id": "user456",
      "action_type": "harm_action",
      "severity": "medium",
      "amount": 25.0,
      "description": "Caused emotional harm",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "repayment_history": []
    }
  ],
  "credits": [
    {
      "_id": "rel_456",
      "debtor_id": "user111",
      "receiver_id": "user123",
      "action_type": "help_action",
      "severity": "minor",
      "amount": 15.0,
      "description": "Provided assistance",
      "status": "active",
      "created_at": "2024-01-14T09:15:00Z",
      "updated_at": "2024-01-14T09:15:00Z",
      "repayment_history": []
    }
  ]
}
```

### Get User's Debts

**GET** `/api/v1/rnanubandhan/{user_id}/debts`

Get all karmic debts for a user (where the user is the debtor).

#### Parameters
- `user_id` (path): The ID of the user
- `status` (query, optional): Filter by status (active, repaid, transferred)

#### Response
```json
{
  "status": "success",
  "user_id": "user123",
  "debts": [
    {
      "_id": "rel_123",
      "debtor_id": "user123",
      "receiver_id": "user456",
      "action_type": "harm_action",
      "severity": "medium",
      "amount": 25.0,
      "description": "Caused emotional harm",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "repayment_history": []
    }
  ]
}
```

### Get User's Credits

**GET** `/api/v1/rnanubandhan/{user_id}/credits`

Get all karmic credits for a user (where the user is the receiver).

#### Parameters
- `user_id` (path): The ID of the user
- `status` (query, optional): Filter by status (active, repaid, transferred)

#### Response
```json
{
  "status": "success",
  "user_id": "user123",
  "credits": [
    {
      "_id": "rel_456",
      "debtor_id": "user111",
      "receiver_id": "user123",
      "action_type": "help_action",
      "severity": "minor",
      "amount": 15.0,
      "description": "Provided assistance",
      "status": "active",
      "created_at": "2024-01-14T09:15:00Z",
      "updated_at": "2024-01-14T09:15:00Z",
      "repayment_history": []
    }
  ]
}
```

### Create Karmic Debt Relationship

**POST** `/api/v1/rnanubandhan/create-debt`

Create a new karmic debt relationship between two users.

#### Request Body
```json
{
  "debtor_id": "user123",
  "receiver_id": "user456",
  "action_type": "harm_action",
  "severity": "medium",
  "amount": 25.0,
  "description": "Caused emotional harm"
}
```

#### Response
```json
{
  "status": "success",
  "message": "Karmic debt relationship created successfully",
  "relationship": {
    "_id": "rel_789",
    "debtor_id": "user123",
    "receiver_id": "user456",
    "action_type": "harm_action",
    "severity": "medium",
    "amount": 25.0,
    "description": "Caused emotional harm",
    "status": "active",
    "created_at": "2024-01-15T11:45:00Z",
    "updated_at": "2024-01-15T11:45:00Z",
    "repayment_history": []
  }
}
```

### Repay Karmic Debt

**POST** `/api/v1/rnanubandhan/repay-debt`

Repay a portion or all of a karmic debt.

#### Request Body
```json
{
  "relationship_id": "rel_123",
  "amount": 10.0,
  "repayment_method": "atonement"
}
```

#### Response
```json
{
  "status": "success",
  "message": "Karmic debt repayment processed successfully",
  "relationship": {
    "_id": "rel_123",
    "debtor_id": "user123",
    "receiver_id": "user456",
    "action_type": "harm_action",
    "severity": "medium",
    "amount": 15.0,
    "description": "Caused emotional harm",
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T12:00:00Z",
    "repayment_history": [
      {
        "amount": 10.0,
        "method": "atonement",
        "timestamp": "2024-01-15T12:00:00Z"
      }
    ]
  }
}
```

### Transfer Karmic Debt

**POST** `/api/v1/rnanubandhan/transfer-debt`

Transfer a karmic debt to another user.

#### Request Body
```json
{
  "relationship_id": "rel_123",
  "new_debtor_id": "user789"
}
```

#### Response
```json
{
  "status": "success",
  "message": "Karmic debt transferred successfully",
  "relationship": {
    "_id": "rel_999",
    "debtor_id": "user789",
    "receiver_id": "user456",
    "action_type": "harm_action",
    "severity": "medium",
    "amount": 25.0,
    "description": "Transferred from user123: Caused emotional harm",
    "status": "active",
    "created_at": "2024-01-15T12:15:00Z",
    "updated_at": "2024-01-15T12:15:00Z",
    "repayment_history": []
  }
}
```

### Get Specific Relationship

**GET** `/api/v1/rnanubandhan/relationship/{relationship_id}`

Get details of a specific Rnanubandhan relationship by ID.

#### Parameters
- `relationship_id` (path): The ID of the relationship

#### Response
```json
{
  "status": "success",
  "relationship": {
    "_id": "rel_123",
    "debtor_id": "user123",
    "receiver_id": "user456",
    "action_type": "harm_action",
    "severity": "medium",
    "amount": 25.0,
    "description": "Caused emotional harm",
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "repayment_history": []
  }
}
```

## Severity Levels

Karmic debts are categorized by severity:

- `minor`: Small karmic debts (1-10 units)
- `medium`: Moderate karmic debts (11-50 units)
- `major`: Large karmic debts (51-100 units)
- `maha`: Very large karmic debts (100+ units)

## Action Types

Common action types that create karmic debts:

- `harm_action`: Causing harm to others
- `help_action`: Providing assistance to others
- `cheat`: Dishonest behavior
- `break_promise`: Failing to keep commitments
- `theft`: Taking what doesn't belong to you
- `violence`: Physical or emotional violence
- `false_speech`: Lying or misleading others

## Repayment Methods

Methods for repaying karmic debts:

- `atonement`: Completing prescribed atonement practices
- `service`: Performing selfless service
- `donation`: Making charitable contributions
- `apology`: Sincere apology and reconciliation
- `teaching`: Sharing knowledge or wisdom

## Error Responses

All endpoints may return the following error responses:

- `400 Bad Request`: Invalid request parameters or data
- `404 Not Found`: User or relationship not found
- `500 Internal Server Error`: Unexpected server error

Error response format:
```json
{
  "detail": "Error message describing the problem"
}
```

## Integration Example

### Python Example
```python
import requests

# Get user's Rnanubandhan network
response = requests.get(
    "http://localhost:8000/api/v1/rnanubandhan/user123"
)
network_data = response.json()

# Create a new karmic debt
debt_data = {
    "debtor_id": "user123",
    "receiver_id": "user456",
    "action_type": "help_action",
    "severity": "minor",
    "amount": 10.0,
    "description": "Provided assistance with project"
}

response = requests.post(
    "http://localhost:8000/api/v1/rnanubandhan/create-debt",
    json=debt_data
)
result = response.json()
```

## Game Realm Integration

The Rnanubandhan API is designed for seamless integration with Game Realm systems:

1. **Social Dynamics**: Track player relationships and interactions
2. **Quest Systems**: Create karmic quest lines based on relationships
3. **Reputation Systems**: Implement reputation based on karmic debts
4. **Economy Balance**: Use karmic debts to balance in-game economies
5. **Narrative Progression**: Drive story progression through relationship resolution

## Security Considerations

1. All endpoints require authentication in production environments
2. Input validation prevents injection attacks
3. Rate limiting protects against abuse
4. Data encryption ensures privacy of karmic information