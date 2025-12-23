# Brahmand Unreal Engine Integration Plan
## Centralized Karma Tracker - 5-Day Build

**Integration Partner**: Sachin & Moksh (Brahmand Unreal Engine Team)  
**Integration Type**: Single Authoritative Endpoint  
**Location**: BHIV Core/Bucket  

---

## 🎯 Integration Objective

Build a centralized Karma Tracker system that serves as the **single authoritative endpoint** for all modules:
- **Games** (Unreal Engine multiplayer)
- **InsightFlow** (Analytics)
- **Finance** (Economic systems)
- **Gurukul** (Learning systems)

All Karma events (multiplayer actions, relics, triggers, NPCs, player actions) emit to this central node for:
- Karma computation
- Persistence to MongoDB
- Real-time response signals back to Unreal Engine
- World state influence (relics, NPCs, environmental effects)

---

## 📋 Current System Status

### ✅ Production-Ready Components

| Component | Status | Location |
|-----------|--------|----------|
| **Unified Event Gateway** | ✅ Operational | `/v1/karma/event/` |
| **Event Schema** | ✅ Defined | `handover/data_module/data_schema.json` |
| **Karma Engine** | ✅ Comprehensive | `utils/karma_engine.py` |
| **Database Layer** | ✅ MongoDB Ready | `database.py` |
| **Event Audit Trail** | ✅ Complete | `karma_events` collection |
| **Docker Deployment** | ✅ Ready | `docker-compose.yml` |
| **API Documentation** | ✅ Complete | `docs/unified_event_api.md` |

### 🔄 Adaptation Needed for Unreal Engine

1. **Event Schema Extension** - Add Unreal-specific event types (multiplayer, relics, NPCs, world triggers)
2. **Real-time Response Pipeline** - Synchronous response with world state changes
3. **Unreal API Binding** - HTTP client integration with Unreal Engine's REST plugin
4. **Multiplayer Sync** - Handle concurrent events from multiple players
5. **Performance Optimization** - Sub-100ms response time for real-time gameplay

---

## 📅 5-Day Integration Timeline

### **Day 1-2: Event Schema + Emission Pipeline**

#### Goals:
- Define Unreal-specific Karma Event Schema
- Extend existing `/v1/karma/event/` endpoint
- Create emission pipeline for Unreal → BHIV Core

#### Tasks:

**Day 1 Morning: Schema Design**
- [ ] Workshop with Sachin/Moksh on Unreal event types
- [ ] Map Unreal actions to Karma classifications:
  - **Dridha** (Fixed): NPC relationships, relic bonds, covenant choices
  - **Adridha** (Volatile): Combat actions, resource collection, dialogue choices
  - **Mishra** (Mixed): Quest completions, world exploration, multiplayer interactions
- [ ] Define intent weight system (0.0-2.0) for action intensity
- [ ] Define energy polarity (-1.0 to +1.0) for good/evil alignment

**Day 1 Afternoon: Schema Implementation**
- [ ] Create `schemas/unreal_karma_schema.json`
- [ ] Extend `UnifiedEventRequest` model with Unreal event types
- [ ] Add validation for Unreal-specific fields (multiplayer_session_id, world_zone, npc_id)
- [ ] Update documentation in `docs/unreal_integration.md`

**Day 2 Morning: Emission Pipeline**
- [ ] Create `routes/v1/karma/unreal_event.py` endpoint
- [ ] Implement event batching for multiplayer scenarios (5-10 events/batch)
- [ ] Add request validation middleware for Unreal events
- [ ] Create test harness for emission pipeline

**Day 2 Afternoon: Testing**
- [ ] Unit tests for schema validation
- [ ] Integration tests for event emission
- [ ] Load testing with 50 concurrent events/second
- [ ] Documentation for Unreal-side integration

**Deliverables:**
```
✅ schemas/unreal_karma_schema.json
✅ routes/v1/karma/unreal_event.py
✅ tests/test_unreal_emission.py
✅ docs/unreal_integration.md
```

---

### **Day 3: Karma Computation + Core/Bucket Sync**

#### Goals:
- Adapt Karma Engine for Unreal event types
- Implement real-time computation pipeline
- Sync with BHIV Core/Bucket storage

#### Tasks:

**Day 3 Morning: Karma Engine Adaptation**
- [ ] Extend `utils/karma_engine.py` with Unreal action evaluation
- [ ] Map Unreal events to Purushartha categories:
  - **Dharma**: Helping NPCs, protecting sacred relics, honoring covenants
  - **Artha**: Resource management, economic decisions, wealth distribution
  - **Kama**: Dialogue choices, relationship building, aesthetic choices
  - **Moksha**: Meditation spots, spiritual practices, liberation quests
- [ ] Implement multiplayer karma distribution (party actions split among members)
- [ ] Add NPC relationship tracking with Rnanubandhan (soul bonds)

**Day 3 Afternoon: Core/Bucket Sync**
- [ ] Create `utils/unreal_sync.py` for BHIV Core synchronization
- [ ] Implement event persistence to `karma_events` collection
- [ ] Add real-time aggregation for player karma scores
- [ ] Create background job for karma decay calculations
- [ ] Implement carryover logic for death/rebirth cycles in-game

**Day 3 Evening: Response Signal Design**
- [ ] Design response payload for Unreal Engine consumption
- [ ] Include world state changes (relic activations, NPC attitude shifts)
- [ ] Add karma thresholds for triggering world events
- [ ] Create response caching for frequently accessed data

**Deliverables:**
```
✅ utils/karma_engine.py (extended)
✅ utils/unreal_sync.py
✅ tests/test_unreal_karma_computation.py
✅ Response signal schema documented
```

---

### **Day 4: Unreal API Binding + Multiplayer Sync Tests**

#### Goals:
- Create HTTP client bindings for Unreal Engine
- Test multiplayer synchronization
- Validate real-time response pipeline

#### Tasks:

**Day 4 Morning: Unreal API Binding**
- [ ] Collaborate with Sachin on Unreal HTTP plugin integration
- [ ] Create C++ example code for event emission from Unreal
- [ ] Document authentication mechanism (API keys for game servers)
- [ ] Create Blueprint examples for common karma events
- [ ] Test endpoint connectivity from Unreal dev environment

**Day 4 Afternoon: Multiplayer Sync**
- [ ] Test concurrent event processing (100+ players)
- [ ] Validate event ordering and timestamp handling
- [ ] Test party karma distribution logic
- [ ] Validate NPC relationship updates across player sessions
- [ ] Test relic state synchronization across game world

**Day 4 Evening: Performance Validation**
- [ ] Measure response latency (target: <100ms)
- [ ] Test database write throughput (target: 500 events/sec)
- [ ] Validate event queue handling under load
- [ ] Test error recovery and retry logic
- [ ] Monitor MongoDB performance metrics

**Deliverables:**
```
✅ docs/unreal_client_examples.md (C++ & Blueprint)
✅ tests/test_multiplayer_sync.py
✅ Performance benchmarks documented
✅ API authentication setup guide
```

---

### **Day 5: Stress Test, Cleanup & Final Handoff**

#### Goals:
- Comprehensive stress testing
- Code cleanup and documentation
- Handoff materials for Sachin/Moksh

#### Tasks:

**Day 5 Morning: Stress Testing**
- [ ] Simulate 500+ concurrent players
- [ ] Test sustained event load (1000 events/sec for 10 minutes)
- [ ] Validate MongoDB scaling under load
- [ ] Test failover and recovery scenarios
- [ ] Document performance bottlenecks and optimizations

**Day 5 Afternoon: Cleanup**
- [ ] Code review and refactoring
- [ ] Update all documentation
- [ ] Create migration guide for existing Karma data
- [ ] Add monitoring and observability hooks
- [ ] Create troubleshooting guide

**Day 5 Evening: Handoff**
- [ ] Handoff meeting with Sachin/Moksh
- [ ] Demo of complete integration flow
- [ ] Knowledge transfer session
- [ ] Provide access to monitoring dashboards
- [ ] Create support channel for post-integration issues

**Deliverables:**
```
✅ HANDOFF_TO_UNREAL_TEAM.md
✅ TROUBLESHOOTING_GUIDE.md
✅ Performance test results
✅ Monitoring dashboard access
✅ Production deployment checklist
```

---

## 🔧 Unified Karma Event Schema (Unreal Extension)

### Base Schema (Existing)
```json
{
  "type": "life_event | atonement | appeal | death_event | stats_request",
  "data": { "user_id": "string", "action": "string", "role": "string" },
  "timestamp": "ISO8601",
  "source": "string"
}
```

### Unreal Extension
```json
{
  "type": "unreal_action | multiplayer_event | npc_interaction | relic_event | world_trigger",
  "data": {
    "user_id": "string",
    "multiplayer_session_id": "string (optional)",
    "world_zone": "string",
    "action": "string",
    "action_category": "combat | exploration | dialogue | ritual | economic",
    "intent_weight": 0.0-2.0,
    "energy_polarity": -1.0 to +1.0,
    "karma_classification": "Dridha | Adridha | Mishra",
    "target_entity": {
      "type": "npc | relic | player | environment",
      "id": "string",
      "name": "string"
    },
    "context": {
      "party_members": ["player_id1", "player_id2"],
      "active_quests": ["quest_id1", "quest_id2"],
      "equipped_relics": ["relic_id1", "relic_id2"],
      "world_state": { "time_of_day": "dawn", "moon_phase": "full" }
    }
  },
  "timestamp": "ISO8601",
  "source": "unreal_engine"
}
```

### Response Schema (Unreal-Specific)
```json
{
  "status": "success | failure",
  "event_id": "string",
  "user_karma_delta": {
    "DharmaPoints": 10,
    "PaapTokens": { "minor": 0, "medium": 0, "maha": 0 },
    "DridhaKarma": 5,
    "AdridhaKarma": 3,
    "Rnanubandhan": { "minor": 0, "medium": 0, "major": 2 }
  },
  "world_effects": {
    "relic_activations": [
      { "relic_id": "sacred_sword", "power_level": 1.2, "effect": "blessing_of_dharma" }
    ],
    "npc_attitude_changes": [
      { "npc_id": "village_elder", "attitude_delta": +15, "new_relationship": "friendly" }
    ],
    "environmental_triggers": [
      { "zone": "temple_grounds", "effect": "divine_light", "duration_seconds": 60 }
    ],
    "unlocked_content": [
      { "type": "dialogue_option", "npc_id": "mystic_sage", "dialogue_tree": "path_of_moksha" }
    ]
  },
  "player_state": {
    "current_karma_score": 145,
    "karma_tier": "Dharmic Seeker",
    "next_threshold": { "tier": "Enlightened Soul", "karma_required": 200 },
    "active_atonements": [
      { "plan_id": "atonement_123", "progress": "3/7 tasks", "deadline": "2025-11-01T00:00:00Z" }
    ]
  },
  "timestamp": "ISO8601",
  "processing_time_ms": 45
}
```

---

## 🎮 Example Unreal Event Flows

### Flow 1: Player Helps NPC in Multiplayer
```
1. Player "Arjuna_77" helps wounded NPC "Village_Elder" in party with "Krishna_99"
2. Unreal emits event → /v1/karma/event/

Request:
{
  "type": "npc_interaction",
  "data": {
    "user_id": "Arjuna_77",
    "multiplayer_session_id": "session_abc123",
    "world_zone": "sacred_forest",
    "action": "heal_npc",
    "action_category": "ritual",
    "intent_weight": 1.5,
    "energy_polarity": 0.9,
    "karma_classification": "Dridha",
    "target_entity": { "type": "npc", "id": "village_elder_001", "name": "Elder Bhishma" },
    "context": {
      "party_members": ["Krishna_99"],
      "equipped_relics": ["healing_mantra_scroll"]
    }
  },
  "source": "unreal_engine"
}

3. Karma Engine processes → Returns response with:
   - +15 DharmaPoints to Arjuna_77
   - +8 DharmaPoints to Krishna_99 (party assist)
   - +10 Rnanubandhan.minor bond with Elder Bhishma
   - NPC attitude change: Elder Bhishma → "Grateful" (+20 relationship)
   - Unlock: Dialogue tree "Ancient Wisdom" with Elder Bhishma
   
4. Unreal receives response → Updates:
   - UI karma score indicator
   - Elder Bhishma's behavior tree (now offers quests)
   - Relic "healing_mantra_scroll" gains +0.1 power
   - Environment: Sacred forest glows with divine light (60 seconds)
```

### Flow 2: Player Commits Violence (PvP)
```
1. Player "Ravana_666" attacks player "Rama_108" in PvP zone
2. Unreal emits event → /v1/karma/event/

Request:
{
  "type": "multiplayer_event",
  "data": {
    "user_id": "Ravana_666",
    "multiplayer_session_id": "pvp_arena_xyz",
    "world_zone": "battlefield_kurukshetra",
    "action": "kill_player",
    "action_category": "combat",
    "intent_weight": 1.8,
    "energy_polarity": -0.8,
    "karma_classification": "Adridha",
    "target_entity": { "type": "player", "id": "Rama_108", "name": "Rama the Just" },
    "context": {
      "equipped_relics": ["demon_sword_of_rage"]
    }
  },
  "source": "unreal_engine"
}

3. Karma Engine processes → Returns response with:
   - -25 DharmaPoints to Ravana_666
   - +1 PaapTokens.medium (violence)
   - +15 Rnanubandhan.medium debt to Rama_108
   - -10 AdridhaKarma (volatile negative karma)
   - Auto-generated atonement plan for violence
   
4. Unreal receives response → Updates:
   - UI shows karma drop + "Paap Accumulated" warning
   - "demon_sword_of_rage" relic corrupts (+0.2 dark energy)
   - Environment: Dark clouds gather over player (visual effect)
   - Quest trigger: "Path of Redemption" appears in quest log
   - NPC reactions: Dharmic NPCs become hostile/fearful
```

---

## 🔐 Authentication & Security

### Game Server Authentication
```
- API Key-based authentication for Unreal game servers
- Key rotation every 30 days
- Rate limiting: 1000 requests/minute per game server
- Event signature validation to prevent spoofing
```

### Player Identity Verification
```
- User IDs validated against player session tokens
- Multiplayer session IDs verified with game server registry
- Anti-cheat hooks: Suspicious event patterns flagged for review
```

---

## 📊 Monitoring & Observability

### Key Metrics to Track
```
- Event ingestion rate (events/second)
- Response latency (p50, p95, p99)
- Database write throughput
- Karma computation time
- Error rate by event type
- Multiplayer sync conflicts
```

### Alerting Thresholds
```
- Response latency > 150ms → Warning
- Response latency > 500ms → Critical
- Event ingestion queue depth > 1000 → Warning
- Database connection pool exhaustion → Critical
- Error rate > 1% → Warning
```

---

## 🧪 Testing Strategy

### Unit Tests
- Event schema validation
- Karma computation logic
- Response payload generation
- Error handling

### Integration Tests
- End-to-end event flow
- Database persistence
- Multiplayer party karma distribution
- NPC relationship updates

### Load Tests
- 500 concurrent players
- 1000 events/second sustained load
- Database scaling validation
- MongoDB replica set failover

### Chaos Tests
- Network partition simulation
- Database connection failures
- Event queue overflow
- Malformed event handling

---

## 📚 Handoff Materials for Sachin/Moksh

### Documentation
1. **Integration Guide** - Step-by-step Unreal setup
2. **API Reference** - Complete endpoint documentation
3. **Event Schema Reference** - All event types and fields
4. **Blueprint Examples** - Common karma event patterns
5. **C++ Examples** - HTTP client integration code
6. **Troubleshooting Guide** - Common issues and solutions

### Code Examples
1. **Basic Event Emission** (Blueprint + C++)
2. **Multiplayer Party Events** (Blueprint + C++)
3. **NPC Relationship Tracking** (Blueprint + C++)
4. **Relic Karma Integration** (Blueprint + C++)
5. **Error Handling & Retry Logic** (C++)

### Tools & Access
1. **API Monitoring Dashboard** - Real-time metrics
2. **Event Inspector Tool** - Debug event payloads
3. **Karma Computation Simulator** - Test scenarios
4. **Load Testing Scripts** - Performance validation
5. **Support Channel** - Dedicated Slack/Discord

---

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Unreal Engine                            │
│  (Multiplayer Game Servers + Player Clients)                │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Player 1 │  │ Player 2 │  │ Player N │                  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
│       │             │             │                         │
│       └─────────────┴─────────────┘                         │
│                     │                                        │
│              HTTP Events (JSON)                              │
└─────────────────────┼────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              BHIV Core / Bucket                             │
│           (Karma Tracker - Docker Container)                 │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  FastAPI Server (main.py)                              │ │
│  │                                                          │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │  /v1/karma/event/  (Unified Gateway)             │  │ │
│  │  └────────────────┬─────────────────────────────────┘  │ │
│  │                   │                                     │ │
│  │                   ▼                                     │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │  Event Router (routes/v1/karma/event.py)         │  │ │
│  │  │  - Validates schema                               │  │ │
│  │  │  - Routes to appropriate handler                  │  │ │
│  │  │  - Logs to karma_events collection                │  │ │
│  │  └────────────────┬─────────────────────────────────┘  │ │
│  │                   │                                     │ │
│  │                   ▼                                     │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │  Karma Engine (utils/karma_engine.py)            │  │ │
│  │  │  - Computes Dharma/Paap/Rnanubandhan             │  │ │
│  │  │  - Applies Dridha/Adridha/Mishra classification  │  │ │
│  │  │  - Calculates world effects                       │  │ │
│  │  └────────────────┬─────────────────────────────────┘  │ │
│  │                   │                                     │ │
│  │                   ▼                                     │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │  MongoDB (database.py)                            │  │ │
│  │  │  - users collection                                │  │ │
│  │  │  - karma_events collection                         │  │ │
│  │  │  - transactions collection                         │  │ │
│  │  │  - rnanubandhan_ledger collection                  │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ Response (JSON)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    Unreal Engine                            │
│                 (Response Processor)                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  - Update player UI (karma scores)                   │  │
│  │  - Trigger relic effects                              │  │
│  │  - Update NPC behavior trees                          │  │
│  │  │  - Environmental effects (VFX/SFX)                  │  │
│  │  - Unlock content (dialogues/quests)                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Success Criteria

### Functional Requirements
- ✅ All Unreal event types successfully processed
- ✅ Response time < 100ms for 95% of requests
- ✅ Zero data loss during event processing
- ✅ Multiplayer sync working for 500+ concurrent players
- ✅ NPC relationship updates reflected in real-time
- ✅ Relic effects synchronized across game world

### Non-Functional Requirements
- ✅ System uptime > 99.9%
- ✅ Auto-scaling based on player load
- ✅ Comprehensive monitoring and alerting
- ✅ Complete API documentation
- ✅ Handoff materials delivered to Sachin/Moksh
- ✅ Support channel established

---

## 📞 Contact & Support

**Integration Lead**: [Your Name]  
**Unreal Team**: Sachin & Moksh  
**Support Channel**: #karma-unreal-integration  
**Documentation**: `/docs/unreal_integration.md`  

---

## 🙏 Reflections

> "Keep structure clean, reflections pure, and ensure Karma logic flows consistently across systems."

This integration bridges the spiritual depth of Karma philosophy with the dynamic world of Unreal Engine, creating a living system where player actions have meaningful, persistent consequences that shape not just the game world, but the player's journey through cycles of cause and effect.

May this system serve as a bridge between ancient wisdom and modern technology, creating experiences that are both entertaining and spiritually enriching.

**Hari Om Tat Sat** 🕉️
