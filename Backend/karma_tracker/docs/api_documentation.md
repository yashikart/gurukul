# KarmaChain API Documentation

## Overview

KarmaChain is a Vedic-based karma tracking system built with FastAPI and MongoDB. It provides a comprehensive API for tracking user actions, calculating karma/merit scores, and implementing progressive punishment and atonement mechanisms based on traditional Vedic principles.

### Key Features
- **Dual-ledger system**: Separate tracking of karma and merit
- **Vedic classification**: Four-tier karma system (Minor, Medium, Major, Maha)
- **Progressive atonement**: Jap, Tap, Bhakti, and Daan mechanisms
- **Unified event gateway**: Single endpoint for all karma operations
- **Comprehensive testing**: Full test suite with integration demos

## Base URL

```
http://localhost:8000/v1/karma
```

## Authentication

Authentication is not implemented in this version. It should be handled by the integrating system.

## Health Check

#### GET /health

Check if the API is running and healthy.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Endpoints

### Unified Event Gateway

#### POST /v1/karma/event

Process any karma-related event through a single unified gateway. This endpoint provides a single entry point for all karma operations with automatic event logging and audit trail.

**Request Body:**
```json
{
  "type": "string",  // Event type: "life_event", "atonement", "appeal", "death_event", "stats_request"
  "data": {},        // Event-specific data
  "timestamp": "ISO 8601 datetime",  // Optional, defaults to current time
  "source": "string"  // Optional, identifies the source system
}
```

**Supported Event Types:**
- **life_event**: Log user actions (maps to `/log-action`)
- **atonement**: Submit atonement proof (maps to `/atonement/submit`)
- **atonement_with_file**: Submit atonement with file upload (maps to `/atonement/submit-with-file`)
- **appeal**: Request karma appeal (maps to `/appeal`)
- **death_event**: Process user death events (maps to `/death/event`)
- **stats_request**: Get user statistics (maps to `/stats/{user_id}`)

**Response:**
```json
{
  "status": "success",
  "event_type": "string",
  "message": "string",
  "data": {},
  "timestamp": "ISO 8601 datetime",
  "routing_info": {
    "internal_endpoint": "string",
    "mapped_from": "string"
  }
}
```

#### POST /v1/karma/event/with-file

Submit events with file attachments, currently supporting atonement submissions with proof files.

**Request Body (multipart/form-data):**
```
event_type: "atonement_with_file"
user_id: "string"
plan_id: "string"
atonement_type: "string"
amount: "number"
proof_text: "string" (optional)
tx_hash: "string" (optional)
proof_file: File (optional)
```

**File Upload Requirements:**
- Maximum file size: 1MB (configurable via `MAX_FILE_SIZE`)
- Supported file types: pdf, jpg, jpeg, png, txt
- Files are stored temporarily and cleaned up automatically
- Upload timeout: 30 seconds (configurable via `FILE_UPLOAD_TIMEOUT`)

**Response:**
```json
{
  "status": "success",
  "event_type": "atonement_with_file",
  "message": "Atonement submitted successfully",
  "data": {
    "atonement_id": "string",
    "progress": {},
    "completed": "boolean"
  },
  "timestamp": "ISO 8601 datetime",
  "routing_info": {
    "internal_endpoint": "/v1/karma/atonement/submit-with-file",
    "mapped_from": "atonement_with_file"
  }
}
```

### Action Logging

#### POST /v1/karma/log-action

Log a user action and process karma changes based on Vedic classification.

**Request Body:**
```json
{
  "user_id": "string",
  "role": "string",
  "action": "string",
  "note": "string"  // Optional
}
```

**Response:**
```json
{
  "status": "success",
  "action": "string",
  "intent": "string",
  "reward": 0,
  "merit_score": 0,
  "role": "string",
  "karma_classification": "minor|medium|major|maha",
  "paap_tokens_awarded": 0,
  "merit_tokens_awarded": 0
}
```

**Karma Classifications:**
- **Minor**: Small good/bad deeds (helping neighbor, white lies)
- **Medium**: Significant deeds (charity, disrespect)  
- **Major**: Serious deeds (teaching dharma, grave harm)
- **Maha**: Extreme deeds (spiritual guidance, heinous crimes)

### Appeals

#### POST /v1/karma/appeal

Submit an appeal against a karma action.

**Request Body:**
```json
{
  "user_id": "string",
  "action_id": "string",
  "reason": "string",
  "evidence": "string"  // Optional
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Appeal submitted successfully",
  "appeal_id": "string"
}
```

#### GET /v1/karma/appeal/{appeal_id}

Get details of a specific appeal.

**Response:**
```json
{
  "_id": "string",
  "user_id": "string",
  "action_id": "string",
  "reason": "string",
  "evidence": "string",
  "status": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Atonement

#### POST /v1/karma/atonement

Request an atonement plan for a specific paap (sin) based on Vedic principles.

**Request Body:**
```json
{
  "user_id": "string",
  "paap_type": "string"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Atonement plan created",
  "atonement_id": "string",
  "plan": {
    "jap": {
      "mantra": "string",
      "repetitions": 108,
      "completed": 0
    },
    "tap": {
      "duration_days": 3,
      "type": "fasting",
      "completed": false
    },
    "bhakti": {
      "acts_required": 1,
      "acts_completed": 0,
      "act_types": ["temple_visit", "prayer", "service"]
    },
    "daan": {
      "percentage": 5,
      "amount": 0,
      "completed": false
    }
  },
  "total_severity": "minor|medium|major|maha",
  "estimated_completion": "datetime"
}
```

**Atonement Mechanisms:**
- **Jap**: Mantra repetition (108, 540, 1080 repetitions based on severity)
- **Tap**: Fasting and self-discipline (3, 7, 14 days based on severity)
- **Bhakti**: Devotional acts (1, 3, 7 acts based on severity)
- **Daan**: Charitable giving (5%, 10%, 20% of income based on severity)

#### GET /v1/karma/atonement/{atonement_id}

Get details of a specific atonement plan.

**Response:**
```json
{
  "_id": "string",
  "user_id": "string",
  "paap_type": "string",
  "plan": {},
  "status": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Death Events

#### POST /v1/karma/death

Record a death event for a user.

**Request Body:**
```json
{
  "user_id": "string",
  "cause": "string",  // Optional
  "details": {}       // Optional
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Death event recorded",
  "death_id": "string"
}
```

### User Stats

#### GET /v1/karma/stats/{user_id}

Get karma statistics for a specific user.

**Response:**
```json
{
  "user_id": "string",
  "role": "string",
  "merit_score": 0,
  "token_balances": {},
  "transaction_count": 0,
  "recent_transactions": []
}
```

## Integration Guide

### Quick Start (Local Development)

#### Option 1: Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f karma-api

# Stop services
docker-compose down
```

#### Option 2: Local Development

1. **Windows Setup**:
   ```batch
   scripts\run_local.bat
   ```

2. **Linux/Mac Setup**:
   ```bash
   chmod +x scripts/run_local.sh
   ./scripts/run_local.sh
   ```

3. **Manual Setup**:
   ```bash
   # Create virtual environment
   python -m venv myenv
   source myenv/bin/activate  # Linux/Mac
   myenv\Scripts\activate     # Windows
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Start application
   python main.py
   ```

### Docker Deployment

1. Clone the repository
2. Configure environment variables in `.env` file
3. Run `docker-compose up -d`

### API Integration Best Practices

1. **Use Unified Event Gateway**: For most operations, use `/v1/karma/event` for simplified integration
2. **Error Handling**: Implement proper error handling for all API calls
3. **Testing**: Use the comprehensive test suite before production deployment
4. **Monitoring**: Check `/health` endpoint for system status

### Testing Integration

```bash
# Run comprehensive integration demo
python tests/integration_demo.py

# Run full test suite
python test_runner.py

# Run specific test categories
pytest tests/ -v -m "integration"

# Test unified event system
python test_unified_event_with_db.py

# Test file upload functionality
python test_atonement_storage.py

# Test event endpoints
python test_event_endpoint.py

# Run tests in Docker environment
docker-compose exec karma-api pytest
docker-compose exec karma-api python test_runner.py
```

### Error Handling

All endpoints return appropriate HTTP status codes:
- **200**: Success
- **400**: Bad request (invalid parameters)
- **404**: Resource not found
- **500**: Server error

Error responses include a `detail` field with error information.

**Common Error Responses:**
```json
{
  "detail": "User not found",
  "status_code": 404
}
```

**Unified Event Gateway Error Codes:**
- **K017**: Invalid event type
- **K018**: Missing required fields in event data
- **K019**: File upload validation failed
- **K020**: Event processing timeout
- **K021**: Event storage failed

### Rate Limiting

Rate limiting is configurable via environment variables:
- Default rate limit: 1000 requests per hour per IP
- File uploads may have separate rate limits based on size
- Rate limit headers included in all responses

### Security Considerations

- Authentication should be implemented by the integrating system
- HTTPS should be used in production
- API keys or tokens should be used for authentication
- Input validation is performed on all endpoints
- File uploads are validated for type, size, and content
- All events are logged for audit and security monitoring