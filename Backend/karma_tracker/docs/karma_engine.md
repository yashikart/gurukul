# Karma Engine Documentation

## Overview

The Karma Engine is a predictive karmic evaluation system that assesses actions based on their karmic impact and provides corrective guidance. It integrates with the existing Q-learning framework to simulate behavior learning and incorporates the Purushartha philosophy (Dharma, Artha, Kama, Moksha) as modifiers.

## Core Components

### 1. Karma Scoring Algorithm

The engine evaluates each action based on:

- **Positive/Negative Impact**: Determines if an action generates merit (DharmaPoints, SevaPoints, PunyaTokens) or demerit (PaapTokens)
- **Dridha vs Adridha Influence**: Classifies actions based on behavioral stability (DridhaKarma) vs volatility (AdridhaKarma)
- **Sanchita/Prarabdha/Rnanubandhan Weights**: Links actions to long-term karmic consequences

### 2. Purushartha-Based Scoring

Actions are evaluated against the four Purushartha categories:

- **Dharma** (Righteousness, duty): Modifier 1.2
- **Artha** (Wealth, prosperity): Modifier 1.0
- **Kama** (Desire, pleasure): Modifier 0.8
- **Moksha** (Liberation, spiritual freedom): Modifier 1.5

### 3. Corrective Guidance System

Based on karmic evaluations, the engine recommends corrective practices:

- **Seva** (Selfless service)
- **Meditation** (Mindfulness practice)
- **Daan** (Charitable giving)
- **Tap** (Austerities)
- **Bhakti** (Devotional practices)

### 4. Q-Learning Integration

The karma engine integrates with the existing Q-learning framework to adjust rewards based on karmic factors, simulating behavior learning.

## Key Functions

### `evaluate_action_karma(user_doc, action, intensity)`
Evaluates the karmic impact of an action.

**Parameters:**
- `user_doc` (dict): User document from database
- `action` (str): The action being evaluated
- `intensity` (float): Intensity of the action (0.0 to 2.0)

**Returns:**
- `dict`: Detailed karmic evaluation including scores and recommendations

### `calculate_net_karma(user_doc)`
Calculates the net karma for a user based on all karma types.

**Parameters:**
- `user_doc` (dict): User document from database

**Returns:**
- `dict`: Comprehensive karma calculation with breakdown

### `determine_corrective_guidance(user_doc)`
Determines corrective guidance based on user's overall karma profile.

**Parameters:**
- `user_doc` (dict): User document from database

**Returns:**
- `list`: List of corrective guidance recommendations

### `integrate_with_q_learning(user_doc, action, reward)`
Integrates karma adjustments with Q-learning scaffold.

**Parameters:**
- `user_doc` (dict): User document from database
- `action` (str): The action taken
- `reward` (float): Base reward from Q-learning

**Returns:**
- `tuple`: (adjusted_reward, next_role)

### `get_purushartha_score(user_doc)`
Calculates the Purushartha alignment score for a user.

**Parameters:**
- `user_doc` (dict): User document from database

**Returns:**
- `dict`: Purushartha scores for each category

## Karma Types

### Traditional Karma Types
- **DharmaPoints**: Points earned through learning and following dharmic principles
- **SevaPoints**: Points earned through service to others
- **PunyaTokens**: Tokens earned through selfless service and extraordinary acts
- **PaapTokens**: Negative tokens accumulated through harmful actions (with severity levels)

### Advanced Karma Types
- **DridhaKarma**: Weighted behavioral changeability - strong karma that is difficult to change
- **AdridhaKarma**: Weighted behavioral changeability - weak karma that is easier to change
- **SanchitaKarma**: Accumulated past karma from previous lives
- **PrarabdhaKarma**: Current life karma being experienced
- **Rnanubandhan**: Karmic debts and past obligations (with severity levels)

## Usage Examples

```python
# Evaluate an action
result = evaluate_action_karma(user_doc, "completing_lessons", 1.0)
print(f"Net karma impact: {result['net_karma']}")

# Calculate overall karma
karma_summary = calculate_net_karma(user_doc)
print(f"Net karma: {karma_summary['net_karma']}")

# Get corrective guidance
recommendations = determine_corrective_guidance(user_doc)
for rec in recommendations:
    print(f"Recommend: {rec['practice']} - {rec['reason']}")

# Integrate with Q-learning
adjusted_reward, next_role = integrate_with_q_learning(user_doc, "helping_peers", 10.0)
```

## Testing

Unit tests are available in `tests/test_karma_engine.py` and can be run with:

```bash
python tests/test_karma_engine.py
```