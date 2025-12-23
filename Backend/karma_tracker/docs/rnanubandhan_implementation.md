# Rnanubandhan Implementation Guide

## Overview

Rnanubandhan (karmic debt relationships) is a core concept in the KarmaChain system that models the invisible bonds connecting individuals through their actions. This implementation creates a relational karma model that tracks debts, repayments, and transfers between users.

## Architecture

### Core Components

1. **RnanubandhanManager**: Central class for managing karmic debt relationships
2. **Database Collection**: `rnanubandhan_relationships` collection in MongoDB
3. **API Routes**: RESTful endpoints for relationship management
4. **Integration Points**: Hooks into existing karma logging and atonement systems

### Data Model

Each Rnanubandhan relationship is represented by a document with the following structure:

```json
{
  "_id": "ObjectId",
  "debtor_id": "string",           // User who owes the debt
  "receiver_id": "string",         // User to whom the debt is owed
  "action_type": "string",         // Type of action that created the debt
  "severity": "string",            // Severity level (minor, medium, major, maha)
  "amount": "number",              // Amount of karmic debt
  "description": "string",         // Description of the debt
  "status": "string",              // active, repaid, transferred
  "created_at": "datetime",        // When the relationship was created
  "updated_at": "datetime",        // When the relationship was last updated
  "repayment_history": [           // History of repayments
    {
      "amount": "number",
      "method": "string",
      "timestamp": "datetime"
    }
  ]
}
```

## Implementation Details

### 1. Database Integration

The Rnanubandhan system adds a new collection to the existing MongoDB setup:

```python
# In database.py
rnanubandhan_col = db["rnanubandhan_relationships"]
```

### 2. Core Manager Class

The `RnanubandhanManager` class in `utils/rnanubandhan.py` provides all core functionality:

#### Key Methods

- `create_debt_relationship()`: Creates a new karmic debt between users
- `get_user_debts()`: Retrieves all debts for a user (where user is debtor)
- `get_user_credits()`: Retrieves all credits for a user (where user is receiver)
- `get_network_summary()`: Provides a summary of a user's karmic network
- `repay_debt()`: Processes repayment of a karmic debt
- `transfer_debt()`: Transfers a debt to another user
- `get_relationship_by_id()`: Retrieves a specific relationship by ID

### 3. API Endpoints

RESTful API endpoints are provided in `routes/rnanubandhan.py`:

#### Main Endpoints

- `GET /api/v1/rnanubandhan/{user_id}`: Get user's complete network
- `GET /api/v1/rnanubandhan/{user_id}/debts`: Get user's debts
- `GET /api/v1/rnanubandhan/{user_id}/credits`: Get user's credits
- `POST /api/v1/rnanubandhan/create-debt`: Create new debt relationship
- `POST /api/v1/rnanubandhan/repay-debt`: Repay a debt
- `POST /api/v1/rnanubandhan/transfer-debt`: Transfer a debt
- `GET /api/v1/rnanubandhan/relationship/{relationship_id}`: Get specific relationship

### 4. Integration with Existing Systems

#### Log Action Integration

The existing log action system has been enhanced to automatically create Rnanubandhan relationships when:
1. Harmful actions affect other users
2. Cheating affects other users

New fields added to `LogActionRequest`:
- `affected_user_id`: ID of user affected by the action
- `relationship_description`: Description of the relationship

#### Atonement Integration

When users complete atonement, the system can automatically:
1. Reduce karmic debt amounts
2. Mark relationships as repaid
3. Update relationship statuses

## Usage Examples

### Creating a Debt Relationship

```python
from utils.rnanubandhan import rnanubandhan_manager

# Create a debt relationship
relationship = rnanubandhan_manager.create_debt_relationship(
    debtor_id="user123",
    receiver_id="user456",
    action_type="harm_action",
    severity="medium",
    amount=25.0,
    description="Caused emotional harm during disagreement"
)
```

### Repaying a Debt

```python
# Repay part of a debt
updated_relationship = rnanubandhan_manager.repay_debt(
    relationship_id="relationship_id_here",
    amount=10.0,
    repayment_method="atonement"
)
```

### Transferring a Debt

```python
# Transfer a debt to another user
new_relationship = rnanubandhan_manager.transfer_debt(
    relationship_id="relationship_id_here",
    new_debtor_id="user789"
)
```

### Getting Network Summary

```python
# Get a user's network summary
network_summary = rnanubandhan_manager.get_network_summary("user123")
```

## API Usage Examples

### cURL Examples

```bash
# Get user's Rnanubandhan network
curl -X GET "http://localhost:8000/api/v1/rnanubandhan/user123"

# Create a new debt relationship
curl -X POST "http://localhost:8000/api/v1/rnanubandhan/create-debt" \
  -H "Content-Type: application/json" \
  -d '{
    "debtor_id": "user123",
    "receiver_id": "user456",
    "action_type": "help_action",
    "severity": "minor",
    "amount": 10.0,
    "description": "Provided assistance with project"
  }'

# Repay a debt
curl -X POST "http://localhost:8000/api/v1/rnanubandhan/repay-debt" \
  -H "Content-Type: application/json" \
  -d '{
    "relationship_id": "relationship_id_here",
    "amount": 5.0,
    "repayment_method": "atonement"
  }'
```

### Python Examples

```python
import requests

# Get user's network
response = requests.get("http://localhost:8000/api/v1/rnanubandhan/user123")
network_data = response.json()

# Create debt via API
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
```

## Game Realm Integration

The Rnanubandhan system is designed for seamless integration with Game Realm systems:

### Social Dynamics
- Track player relationships and interactions
- Implement reputation systems based on karmic debts
- Create social quest lines based on relationship resolution

### Quest Systems
- Generate quests to repay karmic debts
- Create story-driven atonement paths
- Implement relationship-based achievements

### Economy Balance
- Use karmic debts to balance in-game economies
- Create trading systems based on karmic credits
- Implement debt-based resource allocation

## Security Considerations

### Input Validation
- All API endpoints validate input parameters
- User existence is verified before creating relationships
- Debt amounts are validated to prevent negative values

### Access Control
- In production, endpoints should require authentication
- Users should only be able to manage their own relationships
- Administrative functions should be restricted

### Data Integrity
- Atomic operations ensure data consistency
- Relationship IDs are validated before operations
- Error handling prevents partial updates

## Testing

### Unit Tests
Comprehensive unit tests are provided in `tests/test_rnanubandhan.py`:

- Test debt creation between users
- Test debt repayment functionality
- Test debt transfer mechanisms
- Test network summary calculations
- Test error handling

### Integration Tests
API integration tests are included in `tests/test_karma_api.py`:

- Test RESTful endpoints
- Test relationship creation via API
- Test network retrieval via API

### Test Script
A comprehensive test script is available in `scripts/test_rnanubandhan.py`:

- Demonstrates all core functionality
- Tests both direct function calls and API endpoints
- Provides example usage patterns

## Future Enhancements

### Advanced Analytics
- Relationship clustering and community detection
- Karmic influence propagation modeling
- Predictive relationship analysis

### Visualization
- Graph-based relationship visualization
- Network analysis dashboards
- Real-time relationship monitoring

### Smart Contracts
- Blockchain-based karmic debt recording
- Decentralized relationship management
- Cross-platform karmic portability

## Performance Considerations

### Indexing
- Database indexes on `debtor_id` and `receiver_id` for fast queries
- Compound indexes for status-based filtering
- Time-based indexes for expiration policies

### Caching
- Network summaries can be cached for frequently accessed users
- Relationship data can be cached for active sessions
- Batch operations for bulk relationship updates

## Troubleshooting

### Common Issues

1. **User Not Found**: Ensure both debtor and receiver exist in the system
2. **Invalid Relationship ID**: Verify the relationship ID format and existence
3. **Insufficient Debt Amount**: Repayment amount cannot exceed remaining debt
4. **Same User Error**: Debtor and receiver must be different users

### Debugging Tips

1. Check database logs for MongoDB errors
2. Verify user existence before creating relationships
3. Use the test script to validate functionality
4. Monitor API response codes for error details

## Conclusion

The Rnanubandhan implementation provides a robust foundation for modeling karmic relationships between users. By tracking debts, repayments, and transfers, the system creates a rich network of connections that can drive engagement and meaningful interactions in both spiritual and gaming contexts.