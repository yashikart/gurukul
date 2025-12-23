# KarmaChain Sample Scenario Walkthrough

This document provides a comprehensive walkthrough of the KarmaChain system, demonstrating Purushartha-based scoring, Rnanubandhan relationships, and the complete karmic lifecycle.

## Scenario: The Business Dilemma

**Background**: Arjun, a successful entrepreneur, faces a moral dilemma when his business partner suggests cutting corners on product quality to maximize profits. This scenario demonstrates how KarmaChain evaluates actions across all four Purushartha principles and tracks karmic relationships.

## Step 1: Initial Karma Profile

```bash
# Check Arjun's initial karma profile
curl -X GET "http://localhost:8000/karma/arjun_123"
```

**Response**:
```json
{
  "user_id": "arjun_123",
  "role": "human",
  "total_karma": 750,
  "karma_breakdown": {
    "dharma_points": 250,
    "seva_points": 180,
    "punya_tokens": 200,
    "paap_tokens": 20,
    "dridha_karma": 150,
    "adridha_karma": 100,
    "sanchita_karma": 300,
    "prarabdha_karma": 200,
    "rnanubandhan": 50
  },
  "purushartha_scores": {
    "dharma": 85,
    "artha": 78,
    "kama": 65,
    "moksha": 72
  },
  "recent_actions": [
    {
      "action": "charity_donation",
      "karma_impact": 15,
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## Step 2: The Moral Dilemma Action

Arjun decides to reject his partner's suggestion and maintains product quality, even at the cost of reduced profits.

```bash
# Log Arjun's quality-first decision
curl -X POST "http://localhost:8000/log-action/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "arjun_123",
    "role": "human",
    "action": "maintain_product_quality",
    "note": "Refused to compromise product quality for higher profits",
    "intent": "ethical_business_practice",
    "context": {
      "business_partner": "raj_456",
      "potential_profit_loss": 50000,
      "customer_impact": "positive",
      "long_term_benefit": "brand_reputation"
    }
  }'
```

**Response**:
```json
{
  "user_id": "arjun_123",
  "action_id": "action_789",
  "karma_impact": 45,
  "token_changes": {
    "dharma_points": 25,
    "seva_points": 15,
    "punya_tokens": 20,
    "paap_tokens": -5
  },
  "purushartha_evaluation": {
    "dharma": {
      "score": 95,
      "impact": "highly_positive",
      "rationale": "Upholding ethical business practices despite financial pressure"
    },
    "artha": {
      "score": 65,
      "impact": "moderate_negative",
      "rationale": "Short-term profit reduction for long-term brand value"
    },
    "kama": {
      "score": 70,
      "impact": "positive",
      "rationale": "Satisfaction from ethical decision-making"
    },
    "moksha": {
      "score": 88,
      "impact": "highly_positive",
      "rationale": "Reducing karmic debt through righteous action"
    }
  },
  "karmic_relationships": {
    "rnanubandhan_created": {
      "customer_trust": 15,
      "employee_loyalty": 10
    },
    "karmic_debts_resolved": {
      "past_quality_compromises": 5
    }
  },
  "atonement_suggestions": [
    {
      "type": "daan",
      "description": "Support quality education initiatives",
      "units": 3,
      "expected_karma_boost": 10
    }
  ]
}
```

## Step 3: Rnanubandhan Relationship Impact

The decision creates positive karmic bonds with customers and employees.

```bash
# Check the karmic relationship with business partner Raj
curl -X GET "http://localhost:8000/karma/raj_456"
```

**Response**:
```json
{
  "user_id": "raj_456",
  "role": "human",
  "total_karma": 680,
  "rnanubandhan_relationships": {
    "arjun_123": {
      "relationship_type": "business_partner",
      "karmic_debt": -15,
      "nature": "learning_opportunity",
      "resolution_path": "ethical_business_practices"
    }
  },
  "recent_influences": [
    {
      "influencer": "arjun_123",
      "action": "maintain_product_quality",
      "karmic_impact": "positive_example",
      "lesson": "ethical_decision_making"
    }
  ]
}
```

## Step 4: Q-Learning Adaptation

The system learns from this interaction and updates its recommendations.

```bash
# Check Q-learning recommendations for similar future scenarios
curl -X POST "http://localhost:8000/v1/karma/event" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "stats_request",
    "user_id": "arjun_123",
    "data": {
      "query_type": "q_learning_predictions",
      "scenario": "business_ethics_dilemma"
    }
  }'
```

**Response**:
```json
{
  "predictions": {
    "maintain_quality": {
      "probability": 0.85,
      "expected_karma_outcome": "highly_positive",
      "confidence": 0.92,
      "historical_success_rate": 0.88
    },
    "compromise_quality": {
      "probability": 0.15,
      "expected_karma_outcome": "negative",
      "confidence": 0.95,
      "historical_success_rate": 0.12,
      "recommended_atonement": "significant_daan_and_bhakti"
    }
  },
  "q_table_updates": {
    "ethical_business_state": {
      "action_values": {
        "maintain_quality": 0.85,
        "compromise_quality": 0.15
      },
      "learning_rate": 0.1,
      "discount_factor": 0.9
    }
  }
}
```

## Step 5: Atonement Opportunity

Arjun decides to further enhance his karma through atonement.

```bash
# Submit atonement for business prosperity
curl -X POST "http://localhost:8000/submit-atonement/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "arjun_123",
    "plan_id": "atonement_plan_123",
    "atonement_type": "daan",
    "units_completed": 5,
    "description": "Donated to support quality education for underprivileged students",
    "supporting_evidence": {
      "receipt_number": "DONATION_2024_001",
      "amount": 10000,
      "beneficiary": "Education_Foundation",
      "impact": "25_students_supported"
    }
  }'
```

**Response**:
```json
{
  "user_id": "arjun_123",
  "atonement_id": "atonement_456",
  "success": true,
  "karma_adjustments": {
    "dharma_points": 30,
    "seva_points": 25,
    "punya_tokens": 35,
    "paap_tokens_reduction": 8
  },
  "purushartha_impact": {
    "dharma": 12,
    "artha": 8,
    "kama": 6,
    "moksha": 15
  },
  "q_learning_update": {
    "atonement_effectiveness": 0.89,
    "future_recommendation_boost": 0.15
  },
  "rnanubandhan_resolution": {
    "educational_debt": 15,
    "societal_contribution": 20
  }
}
```

## Step 6: Final Karma Profile

Check Arjun's updated karma profile after the complete cycle.

```bash
# Check final karma profile
curl -X GET "http://localhost:8000/karma/arjun_123"
```

**Response**:
```json
{
  "user_id": "arjun_123",
  "role": "human",
  "total_karma": 845,
  "karma_breakdown": {
    "dharma_points": 305,
    "seva_points": 220,
    "punya_tokens": 255,
    "paap_tokens": 7,
    "dridha_karma": 165,
    "adridha_karma": 130,
    "sanchita_karma": 335,
    "prarabdha_karma": 220,
    "rnanubandhan": 85
  },
  "purushartha_scores": {
    "dharma": 92,
    "artha": 73,
    "kama": 71,
    "moksha": 85
  },
  "karmic_journey_summary": {
    "actions_taken": [
      {
        "action": "maintain_product_quality",
        "karmic_impact": "highly_positive",
        "purushartha_alignment": "dharma_focused"
      },
      {
        "action": "educational_donation",
        "karmic_impact": "highly_positive",
        "purushartha_alignment": "balanced_all_four"
      }
    ],
    "rnanubandhan_created": [
      "customer_trust_bond",
      "employee_loyalty_bond",
      "educational_support_bond"
    ],
    "karmic_debts_resolved": [
      "past_quality_compromises",
      "educational_opportunity_debt"
    ]
  },
  "q_learning_insights": {
    "ethical_decision_confidence": 0.92,
    "future_recommendations": [
      "continue_quality_focus",
      "expand_educational_support",
      "mentor_young_entrepreneurs"
    ],
    "predicted_karma_trajectory": "upward_positive"
  }
}
```

## Key Insights from the Scenario

### 1. Purushartha Balance
- **Dharma**: Achieved highest score (92) through ethical business practices
- **Artha**: Maintained reasonable score (73) despite short-term profit sacrifice
- **Kama**: Balanced score (71) through satisfaction from ethical decisions
- **Moksha**: High score (85) through karmic debt reduction

### 2. Rnanubandhan Relationships
- **Positive Bonds Created**: Customer trust, employee loyalty, educational support
- **Karmic Debts Resolved**: Past quality compromises, educational opportunity gaps
- **Influence on Others**: Raj's karmic profile shows learning from Arjun's example

### 3. Q-Learning Adaptation
- **Predictive Accuracy**: 92% confidence in ethical decision recommendations
- **Historical Learning**: System learned from Arjun's successful ethical choice
- **Future Guidance**: Personalized recommendations for continued spiritual growth

### 4. Atonement Effectiveness
- **Daan Impact**: Significant karma boost through educational support
- **Multi-purushartha Benefit**: Atonement positively affected all four purushartha
- **Rnanubandhan Resolution**: Educational atonement resolved societal karmic debts

## Vedic Alignment Notes

### Dharma (Righteousness)
- Arjun's decision aligned with *Rita* (cosmic order) and *Satya* (truth)
- Upholding product quality reflects *Dharma* as universal law
- Business ethics demonstrate *Svadharma* (personal duty)

### Artha (Prosperity)
- Long-term brand value outweighs short-term profit maximization
- Ethical business practices create sustainable prosperity
- Resource allocation for education generates societal wealth

### Kama (Desire)
- Fulfillment through ethical satisfaction and societal contribution
- Balanced approach to business desires and spiritual growth
- Desire for meaningful impact over material accumulation

### Moksha (Liberation)
- Reduction of karmic bonds through righteous action
- Progress toward spiritual liberation through ethical living
- Dissolution of past karmic debts through atonement

This scenario demonstrates how KarmaChain provides comprehensive karmic evaluation, tracks relationship impacts, adapts through machine learning, and guides users toward spiritual growth while maintaining practical life balance.