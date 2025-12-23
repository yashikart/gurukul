# Karma Tracker Integration Plan for Gurukul

## Overview
This document outlines the step-by-step plan to integrate Karma Tracker (KarmaChain v2.3) as a microservice into the Gurukul educational platform.

---

## Architecture Decision

**Approach: Microservices Architecture**
- Karma Tracker runs as separate FastAPI service (Port 8008)
- Gurukul backend communicates via HTTP API calls
- Shared MongoDB database for user context
- Frontend displays karma data through Gurukul UI

**Benefits:**
- Separation of concerns
- Independent scaling
- Reusable karma system
- Maintainable codebase

---

## Phase 1: Setup & Configuration

### 1.1 Karma Tracker Service Setup
- [ ] Copy Karma Tracker to Gurukul project structure
- [ ] Configure Karma Tracker to run on port 8008
- [ ] Set up shared MongoDB connection (or configure separate DB)
- [ ] Create startup script for Karma Tracker service
- [ ] Test Karma Tracker service independently

### 1.2 Environment Configuration
- [ ] Add `KARMA_TRACKER_URL` to Gurukul `.env` file
- [ ] Configure CORS to allow Gurukul backend access
- [ ] Set up authentication/API keys if needed
- [ ] Configure MongoDB URI for shared database

### 1.3 Dependencies
- [ ] Add `httpx` or `requests` to Gurukul backend requirements
- [ ] Ensure both services can access MongoDB
- [ ] Test network connectivity between services

---

## Phase 2: Backend Integration Layer

### 2.1 Create Karma Service Client
**File:** `Gurukul_new-main/Backend/Base_backend/karma_service.py`

```python
"""
Karma Tracker Service Client
Handles all communication with Karma Tracker microservice
"""

import httpx
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class KarmaServiceClient:
    def __init__(self):
        self.base_url = os.getenv("KARMA_TRACKER_URL", "http://localhost:8008")
        self.timeout = 30.0
    
    async def log_action(self, user_id: str, action: str, role: str = "learner", 
                        context: Optional[Dict] = None) -> Dict[str, Any]:
        """Log an educational action to karma tracker"""
        pass
    
    async def get_karma_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user's karma profile"""
        pass
    
    async def get_karma_history(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get user's karma history"""
        pass
```

### 2.2 Integration Points
- [ ] Create `karma_service.py` client
- [ ] Add error handling and retry logic
- [ ] Add logging for karma operations
- [ ] Handle service unavailability gracefully

---

## Phase 3: Action Mapping

### 3.1 Educational Actions → Karma Actions Mapping

**File:** `Gurukul_new-main/Backend/Base_backend/karma_action_mapper.py`

```python
"""
Maps Gurukul educational actions to Karma Tracker actions
"""

EDUCATIONAL_TO_KARMA_ACTIONS = {
    # Positive actions
    "lesson_completed": {
        "karma_action": "studying",
        "token": "DharmaPoints",
        "base_value": 10,
        "role": "learner"
    },
    "quiz_passed": {
        "karma_action": "studying",
        "token": "DharmaPoints",
        "base_value": 15,
        "role": "learner"
    },
    "helped_peer": {
        "karma_action": "helping_peers",
        "token": "SevaPoints",
        "base_value": 5,
        "role": "learner"
    },
    "taught_others": {
        "karma_action": "teaching",
        "token": "PunyaTokens",
        "base_value": 20,
        "role": "teacher"
    },
    "completed_assignment": {
        "karma_action": "studying",
        "token": "DharmaPoints",
        "base_value": 12,
        "role": "learner"
    },
    
    # Negative actions
    "cheated_on_test": {
        "karma_action": "cheat",
        "token": "DharmaPoints",
        "base_value": -20,  # Progressive punishment handled by Karma Tracker
        "role": "learner"
    },
    "skipped_lesson": {
        "karma_action": "neglect",
        "token": "DharmaPoints",
        "base_value": -5,
        "role": "learner"
    },
    "plagiarized": {
        "karma_action": "cheat",
        "token": "DharmaPoints",
        "base_value": -30,
        "role": "learner"
    }
}
```

### 3.2 Implementation Tasks
- [ ] Create action mapping dictionary
- [ ] Create mapper function to convert educational events
- [ ] Add intensity calculation (based on quiz score, lesson difficulty, etc.)
- [ ] Handle edge cases and validation

---

## Phase 4: API Endpoints

### 4.1 Gurukul Karma Endpoints

**File:** `Gurukul_new-main/Backend/Base_backend/api.py` (add new endpoints)

```python
@app.get("/api/karma/profile/{user_id}")
async def get_user_karma_profile(user_id: str):
    """Get user's karma profile"""
    pass

@app.get("/api/karma/history/{user_id}")
async def get_user_karma_history(user_id: str, limit: int = 50):
    """Get user's karma history"""
    pass

@app.post("/api/karma/log-action")
async def log_educational_action(action_data: EducationalActionRequest):
    """Log an educational action and update karma"""
    pass

@app.get("/api/karma/leaderboard")
async def get_karma_leaderboard(limit: int = 10):
    """Get karma leaderboard"""
    pass

@app.get("/api/karma/atonement/{user_id}")
async def get_user_atonement_plans(user_id: str):
    """Get user's atonement plans if any"""
    pass
```

### 4.2 Implementation Tasks
- [ ] Add karma endpoints to main API
- [ ] Integrate with karma service client
- [ ] Add authentication/authorization
- [ ] Add request validation
- [ ] Add error handling

---

## Phase 5: Frontend Components

### 5.1 Karma Dashboard Component
**File:** `Gurukul_new-main/new frontend/src/components/KarmaDashboard.jsx`

Features:
- Current karma score display
- Token balances (DharmaPoints, PunyaTokens, SevaPoints)
- Karma trend chart
- Recent actions feed
- Role progression indicator

### 5.2 Karma Profile Page
**File:** `Gurukul_new-main/new frontend/src/pages/KarmaProfile.jsx`

Features:
- Full karma history
- Detailed action breakdown
- Atonement plans (if any)
- Karma statistics
- Lifecycle information

### 5.3 Karma Notifications
**File:** `Gurukul_new-main/new frontend/src/components/KarmaNotification.jsx`

Features:
- Real-time karma updates
- Action feedback ("You earned +10 DharmaPoints!")
- Atonement reminders
- Achievement notifications

### 5.4 Integration Points
- [ ] Add karma dashboard to user profile
- [ ] Show karma score in header/navbar
- [ ] Add karma notifications after actions
- [ ] Create karma leaderboard page
- [ ] Add karma widget to dashboard

---

## Phase 6: Real-time Integration

### 6.1 Action Logging Points

**Educational Events to Track:**
1. **Lesson Completion**
   - Location: `api.py` - lesson completion endpoint
   - Action: `lesson_completed`
   - Karma: +DharmaPoints

2. **Quiz/Test Completion**
   - Location: Test submission endpoints
   - Action: `quiz_passed` or `cheated_on_test` (if detected)
   - Karma: +DharmaPoints or -DharmaPoints

3. **Peer Interaction**
   - Location: Chat/forum endpoints
   - Action: `helped_peer` (if helping detected)
   - Karma: +SevaPoints

4. **Assignment Submission**
   - Location: Assignment endpoints
   - Action: `completed_assignment` or `plagiarized` (if detected)
   - Karma: +DharmaPoints or -DharmaPoints

5. **Teaching Activity**
   - Location: Teaching/mentoring endpoints
   - Action: `taught_others`
   - Karma: +PunyaTokens

### 6.2 Implementation Tasks
- [ ] Add karma logging to lesson completion
- [ ] Add karma logging to quiz submission
- [ ] Add karma logging to peer help detection
- [ ] Add karma logging to assignment submission
- [ ] Add karma logging to teaching activities
- [ ] Add error handling for failed karma updates (non-blocking)

---

## Phase 7: Testing & Validation

### 7.1 Unit Tests
- [ ] Test karma service client
- [ ] Test action mapping logic
- [ ] Test API endpoints
- [ ] Test error handling

### 7.2 Integration Tests
- [ ] Test end-to-end action logging
- [ ] Test karma profile retrieval
- [ ] Test leaderboard functionality
- [ ] Test atonement flow

### 7.3 User Acceptance Testing
- [ ] Verify karma updates appear correctly
- [ ] Verify dashboard displays accurate data
- [ ] Test notification system
- [ ] Verify leaderboard accuracy

---

## Phase 8: Deployment & Monitoring

### 8.1 Deployment
- [ ] Update startup scripts to include Karma Tracker
- [ ] Configure production environment variables
- [ ] Set up health checks
- [ ] Configure logging and monitoring

### 8.2 Monitoring
- [ ] Monitor karma service availability
- [ ] Track karma API response times
- [ ] Monitor error rates
- [ ] Set up alerts for service failures

---

## Implementation Order

### Week 1: Foundation
1. Phase 1: Setup & Configuration
2. Phase 2: Backend Integration Layer
3. Phase 3: Action Mapping

### Week 2: Core Features
4. Phase 4: API Endpoints
5. Phase 6: Real-time Integration (basic actions)

### Week 3: Frontend & Polish
6. Phase 5: Frontend Components
7. Phase 6: Complete real-time integration

### Week 4: Testing & Deployment
8. Phase 7: Testing & Validation
9. Phase 8: Deployment & Monitoring

---

## File Structure

```
Gurukul_new-main/
├── Backend/
│   ├── Base_backend/
│   │   ├── karma_service.py          # NEW: Karma service client
│   │   ├── karma_action_mapper.py   # NEW: Action mapping logic
│   │   └── api.py                   # MODIFY: Add karma endpoints
│   └── karma_tracker/               # NEW: Karma Tracker microservice
│       └── (Karma Tracker files)
├── new frontend/
│   └── src/
│       ├── components/
│       │   ├── KarmaDashboard.jsx   # NEW
│       │   └── KarmaNotification.jsx # NEW
│       └── pages/
│           └── KarmaProfile.jsx     # NEW
└── KARMA_TRACKER_INTEGRATION_PLAN.md # This file
```

---

## Success Criteria

✅ Karma Tracker runs as independent microservice
✅ Educational actions automatically log to karma system
✅ Users can view their karma profile in Gurukul UI
✅ Karma leaderboard displays correctly
✅ Atonement plans are accessible
✅ System handles service failures gracefully
✅ Performance impact is minimal (<100ms overhead)

---

## Next Steps

1. Review and approve this plan
2. Start with Phase 1: Setup & Configuration
3. Iterate through phases sequentially
4. Test each phase before moving to next
5. Deploy incrementally

---

## Notes

- Karma updates should be **non-blocking** - if Karma Tracker is down, Gurukul should still function
- Consider using **async/await** for karma API calls to avoid blocking
- Cache karma profiles to reduce API calls
- Use **background tasks** for non-critical karma updates
- Monitor performance impact and optimize as needed

