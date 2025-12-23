# Response Codes Reference

## HTTP Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful request |
| 201 | Created | Resource successfully created |
| 400 | Bad Request | Invalid input parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate submission) |
| 422 | Unprocessable Entity | Valid request but unable to process |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

## Application-Specific Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| K001 | User not found | Verify user_id is correct |
| K002 | Invalid action type | Check documentation for valid action types |
| K003 | Invalid role | Check documentation for valid roles |
| K004 | Appeal already submitted | Check appeal status instead of resubmitting |
| K005 | Action not eligible for appeal | Only certain actions can be appealed |
| K006 | Atonement already in progress | Complete current atonement first |
| K007 | Q-learning adjustment failed | Internal error, contact support |
| K008 | User already deceased | Cannot perform actions for deceased users |
| K009 | Invalid atonement plan | Verify plan_id is correct |
| K010 | Rate limit exceeded | Reduce request frequency |
| K011 | Insufficient atonement proof | Provide more detailed proof |
| K012 | Atonement plan expired | Request new atonement plan |
| K013 | Invalid file upload | Check file format and size |
| K014 | Database connection error | Retry request or contact support |
| K015 | Token calculation error | Internal error, contact support |
| K016 | Merit score calculation error | Internal error, contact support |
| K017 | Invalid event type | Check supported event types for unified gateway |
| K018 | Event processing failed | Check event data format and required fields |
| K019 | File upload error | Check file format, size, and upload requirements |
| K020 | Event routing failed | Internal error, contact support |
| K021 | File size exceeded | Reduce file size or contact support for limits |

## Response Formats

### Success Response Format
All successful responses return the specific data model for each endpoint:

```json
{
  // Endpoint-specific response data
  // See event_payloads.md for detailed response models
}
```

### Error Response Format
All error responses follow this standard format:

```json
{
  "detail": "string"
}
```

### Validation Error Format
For validation errors (400 status):

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "error message",
      "type": "error_type"
    }
  ]
}
```

## Common Error Scenarios

### Action Logging Errors
- **400 Bad Request**: Invalid action or role
- **422 Unprocessable Entity**: Missing required fields
- **500 Internal Server Error**: Database or Q-learning calculation failure

### Appeal Errors
- **400 Bad Request**: User not found or invalid action
- **409 Conflict**: Appeal already submitted for this action
- **422 Unprocessable Entity**: Action not eligible for appeal

### Atonement Errors
- **400 Bad Request**: Invalid user or plan ID
- **409 Conflict**: Atonement already in progress
- **410 Gone**: Atonement plan expired
- **422 Unprocessable Entity**: Insufficient proof provided

### Death Event Errors
- **400 Bad Request**: User not found
- **500 Internal Server Error**: Loka calculation failure

### Statistics Errors
- **400 Bad Request**: User not found
- **500 Internal Server Error**: Statistics calculation failure

### Unified Event Gateway Errors
- **400 Bad Request**: Invalid event type or missing required fields
- **422 Unprocessable Entity**: Invalid event data format
- **500 Internal Server Error**: Event routing or processing failure

### File Upload Errors
- **400 Bad Request**: Invalid file format or missing required fields
- **413 Payload Too Large**: File size exceeds limit
- **422 Unprocessable Entity**: File processing error
- **500 Internal Server Error**: File storage or processing failure

## Retry Strategies

### Retry Immediately
- **429 Too Many Requests**: Wait for rate limit reset
- **500 Internal Server Error**: Temporary server issues

### Retry with Backoff
- **503 Service Unavailable**: Service temporarily unavailable
- **504 Gateway Timeout**: Gateway timeout issues

### Do Not Retry
- **400 Bad Request**: Client-side error
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Permission denied
- **404 Not Found**: Resource not found
- **409 Conflict**: Business logic conflict
- **413 Payload Too Large**: File size limit exceeded
- **422 Unprocessable Entity**: Invalid business logic

## Rate Limiting

### Rate Limit Headers
All responses include rate limiting headers:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Timestamp when limit resets

### Default Limits
- **Development**: 1000 requests per hour per IP
- **Production**: Configurable via API_RATE_LIMIT environment variable

### File Upload Limits
- **Maximum File Size**: Configurable via MAX_FILE_SIZE environment variable (default: 1MB)
- **Supported File Types**: pdf, jpg, jpeg, png, txt
- **Upload Timeout**: Configurable via FILE_UPLOAD_TIMEOUT (default: 30 seconds)

## Health Check Responses

### Health Check Success (200)
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "dependencies": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

## Unified Event Gateway Specific Information

### Event Processing Status
The unified event gateway provides detailed event processing information:

- **Event ID**: Unique identifier for tracking events
- **Routing Information**: Shows which internal endpoint was called
- **Processing Status**: Success, failed, or error states
- **Response Data**: Original response from internal endpoint

### File Upload Processing
File uploads through the unified gateway:

- **Validation**: File type, size, and content validation
- **Storage**: Temporary storage with automatic cleanup
- **Processing**: File processing integrated with event handling
- **Error Handling**: Detailed error messages for upload failures

### Event Storage and Audit Trail
All events processed through the unified gateway are stored in the `karma_events` collection:

- **Complete Audit Trail**: All events logged with full request/response data
- **Event Status Tracking**: Track event lifecycle from pending to processed/failed
- **Error Logging**: Detailed error information for debugging
- **Performance Monitoring**: Event processing time and success rates

### Integration Benefits
Using the unified event gateway provides:

- **Single Entry Point**: One endpoint for all karma events
- **Consistent Error Handling**: Standardized error responses
- **Centralized Logging**: All events stored for audit and analysis
- **Future Compatibility**: New event types can be added without changing API structure

### Health Check Failure (503)
```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "dependencies": {
    "database": "unhealthy",
    "redis": "healthy"
  },
  "errors": [
    "Database connection failed"
  ]
}
```