# Karma Lifecycle Engine Implementation

## Overview

The Karma Lifecycle Engine implements the karmic lifecycle of Birth → Life → Death → Rebirth within the KarmaChain system. This engine manages the progression of users through their karmic journey, handling Prarabdha karma accumulation, death event thresholds, and rebirth with inherited karma.

## Components

### 1. Core Engine (`utils/karma_lifecycle.py`)

The `KarmaLifecycleEngine` class provides the core functionality:

#### Key Methods:
- `get_user_prarabdha(user_id)`: Retrieves the current Prarabdha karma counter
- `update_prarabdha(user_id, increment)`: Updates the Prarabdha karma counter
- `check_death_threshold(user_id)`: Checks if a user has reached the death threshold
- `calculate_sanchita_inheritance(user)`: Calculates karma inheritance based on Sanchita rules
- `generate_new_user_id()`: Generates a new unique user ID for rebirth
- `trigger_death_event(user_id)`: Processes a death event for a user
- `rebirth_user(user_id)`: Processes a user's rebirth with inherited karma

### 2. API Routes (`routes/v1/karma/lifecycle.py`)

Provides RESTful endpoints for interacting with the lifecycle engine:

#### Endpoints:
- `GET /api/v1/karma/lifecycle/prarabdha/{user_id}`: Get current Prarabdha counter
- `POST /api/v1/karma/lifecycle/prarabdha/update`: Update Prarabdha counter
- `POST /api/v1/karma/lifecycle/death/check`: Check death threshold
- `POST /api/v1/karma/lifecycle/death/process`: Process death event
- `POST /api/v1/karma/lifecycle/rebirth/process`: Process rebirth
- `POST /api/v1/karma/lifecycle/simulate`: Simulate lifecycle cycles

### 3. Integration Points

#### Event System Integration
The lifecycle engine integrates with the existing event bus system to publish lifecycle events:
- Death events
- Rebirth events
- Prarabdha updates

#### Existing Modules Integration
- **Event Processing**: Integrated with `routes/v1/karma/event.py` to trigger death events when thresholds are reached
- **Normalization**: Integrated with `routes/normalization.py` to update Prarabdha counters

### 4. Test Suite (`tests/test_karma_lifecycle.py`)

Comprehensive unit tests covering all major functionality:
- Prarabdha counter operations
- Death threshold checking
- Sanchita inheritance calculations
- User rebirth process
- Edge cases and error handling

### 5. Simulation Script (`scripts/lifecycle_simulation.py`)

A demonstration script that simulates 50 karmic cycles, showing the complete lifecycle process.

## Implementation Details

### Prarabdha Counters
Prarabdha karma represents the portion of accumulated karma that is "ripe" for experiencing in the current life. The system tracks this value per user and updates it based on actions.

### Death Event Threshold
When a user's Prarabdha karma drops below -100, they reach the death threshold. At this point:
1. Their loka (realm) is determined based on their net karma
2. A death event is recorded
3. Karma inheritance is calculated

### Karma Inheritance (Sanchita Rules)
Upon death and rebirth, users inherit a portion of their accumulated karma:
- Positive karma carries over at 20%
- Negative karma carries over at 50% (karmic debt is harder to escape)
- The inherited amount becomes their new Sanchita karma

### Rebirth Process
During rebirth:
1. A new unique user ID is generated
2. Inherited karma is applied to the new identity
3. Starting level is determined based on inherited karma
4. Original user is marked as deceased

## Usage Examples

### Updating Prarabdha Karma
```python
from utils.karma_lifecycle import update_prarabdha_counter

# Increase user's Prarabdha by 25.5
new_prarabdha = update_prarabdha_counter("user_123", 25.5)
```

### Checking Death Threshold
```python
from utils.karma_lifecycle import check_death_event_threshold

threshold_reached, details = check_death_event_threshold("user_123")
if threshold_reached:
    print("User has reached death threshold")
```

### Processing Death and Rebirth
```python
from utils.karma_lifecycle import process_death_event, process_rebirth

# Process death event
death_result = process_death_event("user_123")

# Process rebirth
rebirth_result = process_rebirth("user_123")
new_user_id = rebirth_result["new_user_id"]
```

## API Examples

### Get Prarabdha Counter
```bash
curl -X GET "http://localhost:8000/api/v1/karma/lifecycle/prarabdha/user_123"
```

### Update Prarabdha Counter
```bash
curl -X POST "http://localhost:8000/api/v1/karma/lifecycle/prarabdha/update" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_123", "increment": 15.0}'
```

### Simulate Lifecycle
```bash
curl -X POST "http://localhost:8000/api/v1/karma/lifecycle/simulate" \
  -H "Content-Type: application/json" \
  -d '{"cycles": 50}'
```

## Future Enhancements

1. **Configurable Thresholds**: Allow customization of death thresholds based on user roles or realms
2. **Advanced Inheritance Rules**: Implement more sophisticated karma inheritance algorithms
3. **Loka-Specific Mechanics**: Add unique mechanics for different lokas (realms)
4. **Multi-Life Tracking**: Enhanced tracking of user progression across multiple lives
5. **Integration with Other Systems**: Deeper integration with the existing karma calculation and reward systems