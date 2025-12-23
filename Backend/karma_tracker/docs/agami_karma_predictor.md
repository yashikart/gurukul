# Agami Karma Predictor Documentation

## Overview

The Agami Karma Predictor is a sophisticated module that forecasts future karmic outcomes based on current user actions, Q-learning weights, and contextual factors. Agami Karma represents the karmic results that are queued to manifest in the future, providing users with insights into their spiritual trajectory.

## Key Concepts

### Agami Karma (Future Karma)
Agami Karma is the third of the three types of karma in the Vedic system:
- **Sanchita Karma**: Accumulated past karma
- **Prarabdha Karma**: Currently experiencing karma
- **Agami Karma**: Future karma being created through current actions

### Q-Learning Integration
The predictor leverages the existing Q-learning framework to:
- Analyze action-reward patterns
- Predict role progression
- Recommend optimal actions
- Estimate future karma balances

### Context-Aware Purushartha Weighting
The system dynamically adjusts the four Purushartha (goals of human life) weights based on:
- Time of day
- User role
- Environmental context
- Personal goals

## API Endpoints

### Predict Agami Karma

**POST** `/api/v1/agami/predict`

Predict future karmic outcomes for a user.

#### Request Body
```json
{
  "user_id": "user123",
  "scenario": {
    "context": {
      "environment": "gurukul",
      "role": "student",
      "goal": "learning",
      "time_of_day": "morning"
    }
  }
}
```

#### Response
```json
{
  "status": "success",
  "prediction": {
    "user_id": "user123",
    "timestamp": "2024-01-15T14:30:00Z",
    "current_state": {
      "net_karma": 175,
      "merit_score": 250,
      "paap_score": 75,
      "weighted_karma": 320,
      "role": "student",
      "balances": {
        "DharmaPoints": 100,
        "SevaPoints": 80,
        "PunyaTokens": 70,
        "PaapTokens": {
          "minor": 25,
          "medium": 50
        }
      }
    },
    "q_learning_predictions": {
      "best_actions": [
        {
          "action": "completing_lessons",
          "q_value": 0.85,
          "expected_reward": 5,
          "predicted_role_impact": {
            "current_merit": 250,
            "new_merit": 255,
            "merit_change": 5,
            "current_role": "student",
            "predicted_role": "scholar",
            "role_change": true
          }
        }
      ],
      "role_progression": [
        {
          "action": "completing_lessons",
          "from_role": "student",
          "to_role": "scholar",
          "merit_gain": 5
        }
      ],
      "confidence": 0.75
    },
    "agami_karma": {
      "projected_balances": {
        "DharmaPoints": 120,
        "SevaPoints": 90,
        "PunyaTokens": 85
      },
      "projected_merit_score": 305,
      "projected_paap_score": 60,
      "projected_net_karma": 245,
      "projected_role": "scholar",
      "expected_change": 70,
      "time_horizon": "30_days"
    },
    "context_aware_predictions": {
      "context": {
        "environment": "gurukul",
        "role": "student",
        "goal": "learning"
      },
      "purushartha_modifiers": {
        "Dharma": 1.3,
        "Artha": 1.1,
        "Kama": 0.8,
        "Moksha": 1.2
      },
      "adjusted_predictions": "In Gurukul, Artha actions are weighted for learning context"
    },
    "recommendations": [
      {
        "type": "action_recommendation",
        "priority": "high",
        "action": "completing_lessons",
        "reasoning": "High Q-value action (0.85) with expected reward of 5",
        "expected_benefit": {
          "merit_gain": 5,
          "role_progression": true
        }
      }
    ]
  }
}
```

### Get Agami Prediction

**GET** `/api/v1/agami/user/{user_id}`

Get Agami karma prediction for a specific user.

#### Parameters
- `user_id` (path): The ID of the user

#### Response
```json
{
  "status": "success",
  "user_id": "user123",
  "prediction": {
    // Same structure as POST /predict response
  }
}
```

### Update Context Weights

**POST** `/api/v1/agami/context-weights`

Update context-sensitive Purushartha weights.

#### Request Body
```json
{
  "context_key": "student_gurukul",
  "weights": {
    "dharma_weight": 1.4,
    "artha_weight": 1.2,
    "kama_weight": 0.7,
    "moksha_weight": 1.3
  }
}
```

#### Response
```json
{
  "status": "success",
  "message": "Context weights updated for student_gurukul",
  "weights": {
    "dharma_weight": 1.4,
    "artha_weight": 1.2,
    "kama_weight": 0.7,
    "moksha_weight": 1.3
  }
}
```

### Get Context Weights

**GET** `/api/v1/agami/context-weights/{context_key}`

Get context-sensitive Purushartha weights.

#### Parameters
- `context_key` (path): The context key

#### Response
```json
{
  "status": "success",
  "context_key": "student_gurukul",
  "weights": {
    "dharma_weight": 1.3,
    "artha_weight": 1.1,
    "kama_weight": 0.8,
    "moksha_weight": 1.2
  }
}
```

### Get Sample Scenarios

**GET** `/api/v1/agami/scenarios`

Get sample scenarios for Agami prediction.

#### Response
```json
{
  "status": "success",
  "scenarios": {
    "student_in_gurukul": {
      "context": {
        "environment": "gurukul",
        "role": "student",
        "goal": "learning"
      },
      "description": "Student performing Artha actions in Gurukul environment"
    },
    "warrior_in_game_realm": {
      "context": {
        "environment": "game_realm",
        "role": "warrior",
        "goal": "conquest"
      },
      "description": "Warrior performing Kama actions in Game Realm"
    }
  }
}
```

## Context Weight System

The system uses context-sensitive weights stored in `context_weights.json` to adjust Purushartha priorities based on environment and role.

### Default Context Weights
```json
{
  "student_gurukul": {
    "dharma_weight": 1.3,
    "artha_weight": 1.1,
    "kama_weight": 0.8,
    "moksha_weight": 1.2,
    "description": "Student in Gurukul environment - learning-focused weights"
  },
  "warrior_game_realm": {
    "dharma_weight": 1.1,
    "artha_weight": 1.3,
    "kama_weight": 1.2,
    "moksha_weight": 0.9,
    "description": "Warrior in Game Realm - engagement-focused weights"
  }
}
```

### Weight Application

1. **Dharma Weight**: Affects learning, teaching, and righteous actions
2. **Artha Weight**: Affects prosperity, resource management, and practical skills
3. **Kama Weight**: Affects desire fulfillment, relationships, and engagement
4. **Moksha Weight**: Affects spiritual liberation, meditation, and self-realization

## Prediction Methodology

### Q-Learning Analysis
1. Retrieves current Q-table from database
2. Analyzes action-reward patterns for user's current role
3. Ranks actions by expected Q-value
4. Predicts role progression based on merit score changes

### Karma Projection
1. Simulates karma changes from recommended actions
2. Projects 30-day karma trajectory
3. Calculates expected net karma change
4. Predicts future role based on projected merit

### Context Adjustment
1. Loads context-specific Purushartha weights
2. Adjusts action rankings based on environmental factors
3. Provides context-aware recommendations
4. Modifies karma projections for specific scenarios

## Integration Examples

### Python Example
```python
import requests

# Predict Agami karma for a user
prediction_data = {
    "user_id": "user123",
    "scenario": {
        "context": {
            "environment": "gurukul",
            "role": "student",
            "goal": "learning"
        }
    }
}

response = requests.post(
    "http://localhost:8000/api/v1/agami/predict",
    json=prediction_data
)

prediction = response.json()
print(f"Projected role: {prediction['prediction']['agami_karma']['projected_role']}")
print(f"Expected change: {prediction['prediction']['agami_karma']['expected_change']}")
```

### JavaScript Example
```javascript
// Predict Agami karma for a user
const predictionData = {
    user_id: "user123",
    scenario: {
        context: {
            environment: "gurukul",
            role: "student",
            goal: "learning"
        }
    }
};

fetch("http://localhost:8000/api/v1/agami/predict", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify(predictionData)
})
.then(response => response.json())
.then(data => {
    console.log("Projected role:", data.prediction.agami_karma.projected_role);
    console.log("Expected change:", data.prediction.agami_karma.expected_change);
});
```

## Game Realm Integration

The Agami Karma Predictor is designed for seamless integration with Game Realm systems:

### Dynamic Role Progression
- Predicts character advancement paths
- Recommends optimal quest choices
- Balances gameplay progression with karmic growth

### Context-Sensitive Scenarios
- Adjusts predictions for different game environments
- Provides role-specific guidance
- Supports time-based karma effects

### Player Engagement
- Shows future rewards for current actions
- Creates meaningful choice consequences
- Encourages long-term spiritual gameplay

## Testing

### Unit Tests
Comprehensive unit tests are provided in `tests/test_agami_predictor.py`:

- Test prediction accuracy
- Test context weight application
- Test Q-learning integration
- Test error handling

### Integration Tests
API integration tests are included in `tests/test_karma_api.py`:

- Test RESTful endpoints
- Test prediction scenarios
- Test context weight updates

### Sample Test Script
A comprehensive test script is available in `scripts/test_agami_predictor.py`:

- Demonstrates all core functionality
- Tests both direct function calls and API endpoints
- Provides example usage patterns

## Performance Considerations

### Caching
- Q-table can be cached for frequently accessed predictions
- Context weights are loaded once and reused
- User state can be cached for real-time predictions

### Optimization
- Incremental Q-table updates reduce database load
- Batch prediction requests for multiple users
- Asynchronous processing for complex scenarios

## Troubleshooting

### Common Issues

1. **User Not Found**: Ensure the user exists in the system
2. **Q-Table Empty**: System may need more training data
3. **Context Key Not Found**: Verify context weights are defined
4. **Prediction Confidence Low**: More user actions needed for accurate predictions

### Debugging Tips

1. Check database logs for Q-table access errors
2. Verify user existence before making predictions
3. Use the test script to validate functionality
4. Monitor API response codes for error details

## Future Enhancements

### Advanced Analytics
- Machine learning models for improved predictions
- Natural language processing for scenario analysis
- Real-time karma adjustment based on gameplay

### Visualization
- Karma trajectory charts
- Role progression maps
- Context impact visualizations

### Personalization
- Individual learning models for each user
- Adaptive context weight adjustment
- Personalized recommendation engines

## Conclusion

The Agami Karma Predictor provides powerful insights into future karmic outcomes, enabling users to make informed decisions about their spiritual journey. By combining Q-learning algorithms with context-aware analysis, the system offers personalized guidance that adapts to different environments and roles.