# KarmaChain API Notes for Analytics & Research

## Overview
This document provides essential information for the analytics and research team to understand and utilize the KarmaChain API data. The system implements a dual-ledger system with PunyaTokens (merit), SevaPoints (service), and PaapTokens (sin requiring atonement).

## Data Collection Points

### Unified Event Gateway (NEW)
- **Centralized event logging** through `/v1/karma/event/` endpoint
- **Complete audit trail** stored in `karma_events` collection
- **Supports multiple event types**: life_event, atonement, appeal, death_event, stats_request
- **File-based submissions** through `/v1/karma/event/with-file` endpoint
- **Event metadata tracking**: source, status, timestamps, error messages
- **Analytics goldmine**: Every system interaction logged with full context

### User Actions (Transactions)
- All user actions are logged through `/v1/karma/log-action` endpoint
- Each action affects token balances based on action type and intent classification
- Q-learning algorithm predicts next role and adjusts reward/penalty values
- Progressive punishment system for repeated "cheat" actions
- Paap tokens generated for negative actions, requiring atonement

### Appeals Process
- Appeals data collected through `/v1/karma/appeal` endpoint
- Automatically generates personalized atonement plans based on Paap severity
- Contains valuable information about disputed actions and resolution outcomes
- Can be used to analyze fairness perception and system effectiveness

### Atonement Plans
- Generated through `/v1/karma/atonement` endpoints
- Contains personalized tasks for users to recover from negative karma
- Tracks completion status and proof submission
- **File upload support**: Receipts and proof documents (stored as references)
- Useful for analyzing effectiveness of different atonement strategies

### Death Events (Loka Assignment)
- Recorded through `/v1/karma/death/event` endpoint
- Computes loka assignment based on net karma and Paap completion status
- Captures end-of-lifecycle data including carryover for rebirth
- Important for longitudinal studies and reincarnation analysis

## Token System

### PunyaTokens
- Earned through virtuous actions (dharma, honesty, seva)
- Highest weight (1.0) in merit calculation
- Moderate decay rate (0.001)

### SevaPoints
- Earned through community service and helpful actions
- Medium weight (0.8) in merit calculation  
- Higher decay rate (0.002) to encourage consistent service

### PaapTokens
- Generated through negative actions (lying, cheating, violence)
- Negative weight (-0.5) impacts merit score
- Slow decay rate (0.0005) requires active atonement
- Categorized by severity: minor, medium, maha

## Analytics Opportunities

### Unified Event Analytics (NEW)
- **Complete system audit trail**: Every interaction logged with full context
- **Event correlation analysis**: Cross-reference different event types
- **Error pattern identification**: System failure analysis and debugging
- **Performance monitoring**: Response times, success rates, error frequencies
- **User journey reconstruction**: Complete interaction history per user
- **File upload analytics**: Proof submission patterns and validation success

### Behavioral Analysis
- **Action patterns**: Track user behavior across different roles and actions
- **Intent classification accuracy**: Compare predicted vs actual outcomes
- **Token flow analysis**: Monitor Punya/Seva/Paap token movements
- **Progressive punishment effectiveness**: Analyze recidivism rates

### System Performance
- **Q-learning effectiveness**: Measure prediction accuracy and user satisfaction
- **Appeal success rates**: Track dispute resolution outcomes
- **Atonement completion rates**: Analyze task effectiveness and user engagement
- **Loka assignment accuracy**: Validate karma-based destination assignments

### Longitudinal Studies
- **User journey mapping**: Track complete user lifecycle from birth to death
- **Reincarnation patterns**: Analyze carryover effects across lifecycles
- **Karma accumulation patterns**: Study long-term moral development
- **Role progression analysis**: Examine advancement through different roles

## Key Metrics

### Unified Event Metrics (NEW)
- **Event Volume**: Total events processed by type and time period
- **Event Success Rates**: Success/failure/pending ratios per event type
- **Response Times**: Processing time distribution by event type
- **Error Patterns**: Most common failure modes and frequencies
- **File Upload Metrics**: Upload success rates, file sizes, validation results
- **Event Correlation**: Cross-event pattern analysis

### User-Level Metrics
- **Net Karma**: PunyaTokens + SevaPoints - PaapTokens
- **Merit Score**: Weighted calculation of all token balances
- **Role Progression**: Citizen → Contributor → Guardian → Sage based on merit
- **Atonement Completion Rate**: Percentage of completed vs assigned atonements
- **Recidivism Rate**: Repeat offenses after punishment/atonement

## Data Access Guidelines

### MongoDB Collections
- **users**: User profiles and token balances
- **transactions**: Individual karma actions and their outcomes
- **atonements**: Atonement plans and completion status
- **death_events**: Death events and loka assignments
- **karma_events**: Unified event gateway logs - COMPLETE AUDIT TRAIL (NEW)

### Query Examples
```javascript
// Get user action history
db.transactions.find({user_id: "user123"}).sort({timestamp: -1})

// Analyze atonement completion rates
db.atonements.aggregate([
  {"$group": {
    "_id": "$atonement_type",
    "total": {"$sum": 1},
    "completed": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}}
  }}
])

// Study loka assignment patterns
db.death_events.aggregate([
  {"$group": {
    "_id": "$loka",
    "count": {"$sum": 1},
    "avg_karma": {"$avg": "$net_karma"}
  }}
])

// UNIFIED EVENT ANALYTICS (NEW)
// Get complete user interaction history
db.karma_events.find({"data.user_id": "user123"}).sort({timestamp: -1})

// Analyze event success rates by type
db.karma_events.aggregate([
  {"$group": {
    "_id": "$event_type",
    "total": {"$sum": 1},
    "success": {"$sum": {"$cond": [{"$eq": ["$status", "processed"]}, 1, 0]}},
    "failed": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}}
  }}
])

// Study file upload patterns
db.karma_events.find({
  "event_type": "atonement_with_file",
  "data.has_file": true
}).sort({timestamp: -1})

// Error pattern analysis
db.karma_events.aggregate([
  {"$match": {"status": "failed", "error_message": {"$exists": true}}},
  {"$group": {
    "_id": "$error_message",
    "count": {"$sum": 1},
    "event_types": {"$addToSet": "$event_type"}
  }},
  {"$sort": {"count": -1}}
])
```

- Use `/v1/karma/stats/user/{user_id}` for individual user analysis
- Use `/v1/karma/stats/system` for system-wide analytics
- All timestamps are in UTC format
- Token decay applied automatically based on configured rates
- Respect user privacy by anonymizing data for research publications
- Bulk data extraction requires coordination with API team

## Sample Response Formats

See `sample_responses/` directory for actual API response examples:
- `log_action.json` - Action logging response
- `atonement.json` - Atonement submission response  
- `death.json` - Death event/loka assignment response
- `stats.json` - User statistics response

## Contact Information
For questions about data structure, collection methodology, or access to bulk data, contact the KarmaChain development team.