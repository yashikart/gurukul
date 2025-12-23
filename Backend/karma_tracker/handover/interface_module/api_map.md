# KarmaChain API Map

## Base URL
`/v1/karma/`

## Endpoint Map

### Action Logging
- **Endpoint**: `/v1/karma/log-action/`
- **Method**: POST
- **Purpose**: Record user actions that affect karma and compute rewards/penalties
- **Request Model**: `LogActionRequest` (user_id, action, role, note, context, metadata)
- **Response**: Action result with role updates, token rewards, Paap generation status

### Appeals
- **Endpoint**: `/v1/karma/appeal/`
- **Method**: POST
- **Purpose**: Submit karma appeals for Paap token actions
- **Request Model**: `AppealRequest` (user_id, action, context)
- **Response**: Appeal submission with PAAP severity classification and atonement plan

### Appeal Status
- **Endpoint**: `/v1/karma/appeal/status/{user_id}`
- **Method**: GET
- **Purpose**: Retrieve pending and completed atonement plans for a user
- **Response**: List of atonement plans with task details and completion status

### Atonement Submission
- **Endpoint**: `/v1/karma/atonement/submit`
- **Method**: POST
- **Purpose**: Submit atonement proof (text-based)
- **Request Model**: `AtonementSubmission` (user_id, plan_id, proof_text)
- **Response**: Atonement completion status and token balance updates

### Atonement Submission with File
- **Endpoint**: `/v1/karma/atonement/submit-with-file`
- **Method**: POST
- **Purpose**: Submit atonement proof with file upload
- **Request Model**: Multipart form (user_id, plan_id, proof_text, file)
- **Response**: Atonement completion status and token balance updates

### User Atonement Plans
- **Endpoint**: `/v1/karma/atonement/{user_id}`
- **Method**: GET
- **Purpose**: Retrieve all atonement plans for a user
- **Response**: List of atonement plans with detailed task information

### Death Events
- **Endpoint**: `/v1/karma/death/event`
- **Method**: POST
- **Purpose**: Process user death events and compute loka assignment
- **Request Model**: `DeathEventRequest` (user_id)
- **Response**: Loka assignment, carryover details, and Paap token status

### User Statistics
- **Endpoint**: `/v1/karma/stats/{user_id}`
- **Method**: GET
- **Purpose**: Retrieve comprehensive user karma statistics
- **Response**: User stats including token balances, merit score, action statistics

### Unified Event Gateway
- **Endpoint**: `/v1/karma/event/`
- **Method**: POST
- **Purpose**: Unified gateway for all karma events with centralized logging
- **Request Model**: `UnifiedEventRequest` (type, data, timestamp, source, routing_info)
- **Response**: Unified event response with routing information

### Unified Event Gateway with File
- **Endpoint**: `/v1/karma/event/with-file`
- **Method**: POST
- **Purpose**: File-based event submissions through unified gateway
- **Request Model**: Multipart form with event data and file upload
- **Response**: Unified event response with file processing details

### Health Check
- **Endpoint**: `/health`
- **Method**: GET
- **Purpose**: System health and readiness check
- **Response**: Service status and dependency health

### Metrics
- **Endpoint**: `/metrics`
- **Method**: GET
- **Purpose**: Prometheus-compatible metrics endpoint
- **Response**: System metrics in Prometheus format

## Authentication
- Currently no authentication required (development mode)
- Bearer token authentication ready for production deployment
- API key support for service-to-service communication
- Unified event gateway supports same authentication methods

## Rate Limiting
- Configurable via `API_RATE_LIMIT` environment variable
- Default: 1000 requests per hour per IP
- Rate limit headers included in responses
- File uploads may have separate rate limits based on size

## Event Types (Unified Gateway)
The unified event gateway supports the following event types:
- **life_event**: Log user actions (maps to `/log-action`)
- **atonement**: Submit atonement proof (maps to `/atonement/submit`)
- **atonement_with_file**: Submit atonement with file upload (maps to `/atonement/submit-with-file`)
- **appeal**: Request karma appeal (maps to `/appeal`)
- **death_event**: Process user death events (maps to `/death/event`)
- **stats_request**: Get user statistics (maps to `/stats/{user_id}`)

## File Upload Support
- Maximum file size: Configurable via `MAX_FILE_SIZE` (default: 1MB)
- Supported file types: pdf, jpg, jpeg, png, txt
- File uploads are processed through the unified event gateway
- Files are stored temporarily and cleaned up after processing

## Versioning
- Current version: v1
- Version included in URL path
- Breaking changes will increment version number
- Backward compatibility maintained within major versions

## Error Handling
- Standard HTTP status codes
- Application-specific error codes (K001-K010)
- Detailed error messages with resolution suggestions
- Consistent response format across all endpoints