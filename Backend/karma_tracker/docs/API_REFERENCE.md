# KarmaChain API Reference

Complete reference for all KarmaChain API endpoints with request/response examples.

## Base URL
```
http://localhost:8000
```

## Authentication
All endpoints currently support open access. Rate limiting is configurable via environment variables.

---

## Unified Event Gateway

### POST /v1/karma/event
**Description**: Single endpoint for all karma operations with automatic event routing.

#### Supported Event Types:
- `life_event`: Log karma actions and behaviors
- `appeal`: Submit karma appeals  
- `atonement`: Request and complete atonement plans
- `death_event`: Record death events for karma transfer
- `stats_request`: Query user karma statistics

### Life Event Example
**Request:**
```json
POST /v1/karma/event
{
  "event_type": "life_event",
  "user_id": "user123",
  "data": {
    "role": "human",
    "action": "help",
    "description": "Helped a colleague with debugging",
    "impact": "positive",
    "context": "workplace"
  }
}
```

**Response (Success - 200):**
```json
{
  "status": "success",
  "event_id": "evt_abc123",
  "user_id": "user123",
  "karma_change": 5,
  "new_balance": 105,
  "message": "Karma logged successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Response (Error - 400):**
```json
{
  "status": "error",
  "error": "Invalid event data",
  "details": "Missing required field: role",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Appeal Example
**Request:**
```json
POST /v1/karma/event
{
  "event_type": "appeal",
  "user_id": "user123",
  "data": {
    "appeal_type": "karma_correction",
    "reason": "Incorrect karma deduction for helping incident",
    "evidence": "Email thread showing successful help provided",
    "original_event_id": "evt_xyz789",
    "requested_change": 10
  }
}
```

**Response (Success - 200):**
```json
{
  "status": "success",
  "event_id": "evt_def456",
  "appeal_id": "app_abc123",
  "user_id": "user123",
  "message": "Appeal submitted successfully",
  "status": "pending_review",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

### Atonement Example
**Request:**
```json
POST /v1/karma/event
{
  "event_type": "atonement",
  "user_id": "user123",
  "data": {
    "request_type": "atonement_plan",
    "reason": "Need to atone for negative karma from workplace conflict",
    "severity": "moderate",
    "preferred_methods": ["meditation", "charity", "community_service"]
  }
}
```

**Response (Success - 200):**
```json
{
  "status": "success",
  "event_id": "evt_ghi789",
  "atonement_id": "ato_abc123",
  "user_id": "user123",
  "atonement_plan": {
    "tasks": [
      {
        "task_id": "task_001",
        "description": "Meditate for 15 minutes daily for 7 days",
        "karma_value": 3,
        "deadline": "2024-01-22T23:59:59Z"
      },
      {
        "task_id": "task_002", 
        "description": "Donate to a charitable cause",
        "karma_value": 5,
        "deadline": "2024-01-30T23:59:59Z"
      }
    ],
    "total_karma_potential": 8,
    "completion_deadline": "2024-01-30T23:59:59Z"
  },
  "message": "Atonement plan created successfully",
  "timestamp": "2024-01-15T10:40:00Z"
}
```

### Atonement Completion Example
**Request:**
```json
POST /v1/karma/event
{
  "event_type": "atonement",
  "user_id": "user123",
  "data": {
    "atonement_type": "complete",
    "atonement_id": "ato_abc123",
    "completed_tasks": ["task_001", "task_002"],
    "completion_notes": "Successfully completed all meditation sessions and donated to local food bank"
  }
}
```

**Response (Success - 200):**
```json
{
  "status": "success",
  "event_id": "evt_jkl012",
  "atonement_id": "ato_abc123",
  "user_id": "user123",
  "karma_earned": 8,
  "new_balance": 113,
  "completion_status": "fully_complete",
  "message": "Atonement completed successfully",
  "timestamp": "2024-01-20T15:45:00Z"
}
```

### Death Event Example
**Request:**
```json
POST /v1/karma/event
{
  "event_type": "death_event",
  "user_id": "user456",
  "data": {
    "final_karma_balance": 89,
    "death_cause": "natural",
    "reincarnation_role": "human",
    "meritorious_deeds": ["charity_work", "mentoring", "community_service"],
    "major_papa": ["theft", "deception"],
    "loka_destination": "earth"
  }
}
```

**Response (Success - 200):**
```json
{
  "status": "success",
  "event_id": "evt_mno345",
  "user_id": "user456",
  "death_record_id": "death_abc123",
  "final_karma": 89,
  "reincarnation_role": "human",
  "loka_destination": "earth",
  "merit_transactions": [
    {
      "transaction_id": "txn_001",
      "merit_type": "charity_work",
      "value": 15,
      "status": "transferred"
    }
  ],
  "message": "Death event recorded and karma processed",
  "timestamp": "2024-01-15T11:00:00Z"
}
```

### Stats Request Example
**Request:**
```json
POST /v1/karma/event
{
  "event_type": "stats_request",
  "user_id": "user123",
  "data": {
    "stats_type": "comprehensive",
    "include_history": true,
    "time_range": "last_30_days"
  }
}
```

**Response (Success - 200):**
```json
{
  "status": "success",
  "event_id": "evt_pqr678",
  "user_id": "user123",
  "stats": {
    "current_karma": 113,
    "karma_trend": "increasing",
    "recent_actions": [
      {
        "action": "help",
        "karma_change": 5,
        "timestamp": "2024-01-15T10:30:00Z"
      },
      {
        "action": "atonement_completion",
        "karma_change": 8,
        "timestamp": "2024-01-20T15:45:00Z"
      }
    ],
    "atonement_status": {
      "active_plans": 0,
      "completed_plans": 1,
      "total_karma_from_atonement": 8
    },
    "appeals_status": {
      "pending": 0,
      "approved": 1,
      "rejected": 0
    }
  },
  "message": "Statistics retrieved successfully",
  "timestamp": "2024-01-15T11:15:00Z"
}
```

---

## File Upload Endpoint

### POST /v1/karma/event/with-file
**Description**: Submit events with file attachments (primarily for atonement evidence).

**Content-Type**: multipart/form-data

#### Request Format:
- `event_data`: JSON string containing the event details
- `file`: Binary file upload (supported types: jpg, jpeg, png, pdf, doc, docx)

**Request Example:**
```
POST /v1/karma/event/with-file
Content-Type: multipart/form-data

Form Data:
- event_data: {
    "event_type": "atonement_with_file",
    "user_id": "user123",
    "data": {
      "request_type": "atonement_plan",
      "reason": "Need to atone for workplace incident",
      "file_description": "Email evidence showing resolution of conflict"
    }
  }
- file: [Binary file data]
```

**Response (Success - 200):**
```json
{
  "status": "success",
  "event_id": "evt_stu901",
  "file_id": "file_xyz789",
  "user_id": "user123",
  "atonement_id": "ato_def456",
  "file_info": {
    "filename": "conflict_resolution_email.pdf",
    "file_type": "application/pdf",
    "file_size": 24576,
    "upload_timestamp": "2024-01-15T12:00:00Z"
  },
  "atonement_plan": {
    "tasks": [
      {
        "task_id": "task_003",
        "description": "Write apology letter to affected colleague",
        "karma_value": 5,
        "deadline": "2024-01-20T23:59:59Z"
      }
    ],
    "total_karma_potential": 5
  },
  "message": "Atonement request with file uploaded successfully",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

**Response (Error - 400):**
```json
{
  "status": "error",
  "error": "Invalid file type",
  "details": "Only jpg, jpeg, png, pdf, doc, docx files are allowed",
  "received_type": "exe",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

**Response (Error - 413):**
```json
{
  "status": "error",
  "error": "File too large",
  "details": "Maximum file size is 10MB",
  "received_size": 15728640,
  "timestamp": "2024-01-15T12:00:00Z"
}
```

---

## Legacy Endpoints (Still Supported)

### POST /v1/karma/log-action
**Description**: Direct endpoint for logging karma actions (legacy).

**Request:**
```json
POST /v1/karma/log-action
{
  "user_id": "user123",
  "role": "human",
  "action": "help",
  "description": "Helped with debugging",
  "impact": "positive"
}
```

**Response (Success - 200):**
```json
{
  "status": "success",
  "user_id": "user123",
  "karma_change": 5,
  "new_balance": 105,
  "message": "Action logged successfully"
}
```

### POST /v1/karma/appeal
**Description**: Direct endpoint for submitting appeals (legacy).

**Request:**
```json
POST /v1/karma/appeal
{
  "user_id": "user123",
  "appeal_type": "karma_correction",
  "reason": "Incorrect karma deduction",
  "evidence": "Supporting documentation"
}
```

**Response (Success - 200):**
```json
{
  "status": "success",
  "appeal_id": "app_legacy123",
  "message": "Appeal submitted successfully"
}
```

---

## Utility Endpoints

### GET /health
**Description**: Health check endpoint for monitoring system status.

**Response (Success - 200):**
```json
{
  "status": "healthy",
  "service": "karmachain-api",
  "version": "2.1",
  "database": "connected",
  "timestamp": "2024-01-15T12:30:00Z",
  "uptime": "2h 15m 30s"
}
```

**Response (Error - 503):**
```json
{
  "status": "unhealthy",
  "service": "karmachain-api",
  "database": "disconnected",
  "error": "Database connection failed",
  "timestamp": "2024-01-15T12:30:00Z"
}
```

### GET /metrics
**Description**: System metrics and statistics.

**Response (Success - 200):**
```json
{
  "status": "success",
  "metrics": {
    "total_events_processed": 15234,
    "events_last_hour": 45,
    "active_users": 892,
    "average_response_time_ms": 125,
    "file_uploads_total": 234,
    "file_uploads_success_rate": 98.7,
    "database_connections": 12,
    "system_memory_usage_percent": 42.3,
    "disk_usage_percent": 28.7
  },
  "timestamp": "2024-01-15T12:30:00Z"
}
```

---

## Error Response Format

All endpoints return consistent error responses:

```json
{
  "status": "error",
  "error": "Error type/category",
  "details": "Detailed error message",
  "timestamp": "2024-01-15T12:30:00Z",
  "request_id": "req_abc123"  // Optional: for debugging
}
```

## Common Error Codes

| HTTP Code | Error Type | Description |
|-----------|------------|-------------|
| 400 | Bad Request | Invalid request format or missing required fields |
| 404 | Not Found | User or resource not found |
| 413 | Payload Too Large | File upload exceeds size limit |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server processing error |
| 503 | Service Unavailable | Database or service unavailable |

## Rate Limiting

Default rate limits (configurable via environment variables):
- API endpoints: 100 requests per minute per IP
- File uploads: 10 uploads per minute per IP
- Event processing: 1000 events per minute total

## File Upload Limits

- Maximum file size: 10MB (configurable)
- Supported file types: jpg, jpeg, png, pdf, doc, docx
- Files are automatically scanned and validated
- Automatic cleanup of old files based on retention policy

## Event Processing

- Events are processed asynchronously for optimal performance
- All events are logged in the audit trail
- File uploads are processed with additional security validation
- Batch processing is supported for high-volume operations

## Multi-Department Support

The system supports integration across multiple departments:
- **Analytics (BHIV)**: Statistical analysis and reporting
- **Infrastructure (Unreal)**: System monitoring and deployment
- **API Integration (Knowledgebase)**: Documentation and integration support

Each department can use the unified event gateway for consistent integration while maintaining their specific requirements and workflows.