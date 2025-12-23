# Karmic Analytics API Documentation

## Overview

The Karmic Analytics API provides endpoints for accessing karmic trends, generating visualizations, and exporting analytics data for InsightFlow dashboards. These endpoints enable monitoring of karma patterns over time and provide actionable insights for user engagement.

## Base URL

```
http://localhost:8000/api/v1/analytics
```

## Authentication

Authentication is not implemented in this version. It should be handled by the integrating system.

## Endpoints

### GET /karma_trends

Get karmic trends data for DharmaPoints, SevaPoints, PaapTokens, and PunyaTokens over a specified time period.

#### Query Parameters
- `weeks` (integer, optional): Number of weeks to analyze (1-52). Default: 4

#### Response
```json
{
  "status": "success",
  "data": {
    "dharma_seva_trends": [
      {
        "week_start": "2023-01-02T00:00:00",
        "dharma_points": 125,
        "seva_points": 87,
        "paap_tokens": 5,
        "punya_tokens": 42,
        "event_count": 23
      }
    ],
    "paap_punya_trends": [
      {
        "week_start": "2023-01-02T00:00:00",
        "paap_total": 5,
        "punya_total": 42,
        "paap_ratio": 0.106,
        "punya_ratio": 0.894,
        "paap_punya_ratio": 0.119
      }
    ]
  }
}
```

### GET /charts/dharma_seva_flow

Generate a chart showing DharmaPoints/SevaPoints flow over time.

#### Query Parameters
- `weeks` (integer, optional): Number of weeks to analyze (1-52). Default: 4
- `download` (boolean, optional): Whether to provide a download link for the chart. Default: false

#### Response
```json
{
  "status": "success",
  "chart_generated": true,
  "filepath": "./analytics_exports/dharma_seva_flow_20230101_120000.png",
  "timestamp": "2023-01-01T12:00:00Z"
}
```

When `download=true`:
```json
{
  "status": "success",
  "download_url": "/analytics_exports/dharma_seva_flow_20230101_120000.png",
  "filepath": "./analytics_exports/dharma_seva_flow_20230101_120000.png"
}
```

### GET /charts/paap_punya_ratio

Generate a chart showing the Paap/Punya ratio over time.

#### Query Parameters
- `weeks` (integer, optional): Number of weeks to analyze (1-52). Default: 4
- `download` (boolean, optional): Whether to provide a download link for the chart. Default: false

#### Response
```json
{
  "status": "success",
  "chart_generated": true,
  "filepath": "./analytics_exports/paap_punya_ratio_20230101_120000.png",
  "timestamp": "2023-01-01T12:00:00Z"
}
```

When `download=true`:
```json
{
  "status": "success",
  "download_url": "/analytics_exports/paap_punya_ratio_20230101_120000.png",
  "filepath": "./analytics_exports/paap_punya_ratio_20230101_120000.png"
}
```

### GET /exports/weekly_summary

Export weekly summary data to a CSV file.

#### Query Parameters
- `weeks` (integer, optional): Number of weeks to analyze (1-52). Default: 4
- `download` (boolean, optional): Whether to provide a download link for the CSV. Default: true

#### Response
```json
{
  "status": "success",
  "export_generated": true,
  "filepath": "./analytics_exports/weekly_summary_20230101_120000.csv",
  "timestamp": "2023-01-01T12:00:00Z"
}
```

When `download=true`:
```json
{
  "status": "success",
  "download_url": "/analytics_exports/weekly_summary_20230101_120000.csv",
  "filepath": "./analytics_exports/weekly_summary_20230101_120000.csv"
}
```

### GET /metrics/live

Get live karmic metrics for the system.

#### Response
```json
{
  "status": "success",
  "data": {
    "timestamp": "2023-01-01T12:00:00Z",
    "total_users": 1247,
    "events_last_24h": 243,
    "dharma_points_last_24h": 1247,
    "seva_points_last_24h": 876,
    "paap_tokens_last_24h": 23,
    "punya_tokens_last_24h": 432,
    "average_net_karma_sample": 15.7,
    "health_status": "operational"
  }
}
```

## Error Responses

All endpoints return appropriate HTTP status codes:
- **200**: Success
- **400**: Bad request (invalid parameters)
- **404**: Resource not found
- **500**: Server error
- **501**: Not implemented (feature not available)

Error responses include a `detail` field with error information:
```json
{
  "detail": "Error generating trends: Database connection failed"
}
```

## Integration Examples

### Python Example
```python
import requests

# Get karmic trends
response = requests.get("http://localhost:8000/api/v1/analytics/karma_trends?weeks=8")
trends_data = response.json()

# Generate Dharma/Seva flow chart
response = requests.get("http://localhost:8000/api/v1/analytics/charts/dharma_seva_flow?weeks=4&download=true")
chart_data = response.json()
print(f"Download chart from: {chart_data['download_url']}")

# Export weekly summary
response = requests.get("http://localhost:8000/api/v1/analytics/exports/weekly_summary?weeks=4")
export_data = response.json()
print(f"CSV exported to: {export_data['filepath']}")
```

### JavaScript Example
```javascript
// Get live metrics
fetch('http://localhost:8000/api/v1/analytics/metrics/live')
  .then(response => response.json())
  .then(data => {
    console.log('Live metrics:', data.data);
  })
  .catch(error => {
    console.error('Error fetching metrics:', error);
  });

// Get Paap/Punya ratio chart
fetch('http://localhost:8000/api/v1/analytics/charts/paap_punya_ratio?weeks=12&download=true')
  .then(response => response.json())
  .then(data => {
    const img = document.createElement('img');
    img.src = data.download_url;
    document.body.appendChild(img);
  })
  .catch(error => {
    console.error('Error generating chart:', error);
  });
```

## Scheduled Exports

The system automatically generates weekly summary exports based on the configuration in `ANALYTICS_SCHEDULE_DAY` and `ANALYTICS_SCHEDULE_TIME` environment variables. By default, exports are generated every Monday at 1:00 AM.

## File Storage

Generated charts and CSV exports are stored in the `analytics_exports` directory. This directory is served statically at the `/analytics_exports` endpoint, allowing direct access to generated files via their download URLs.

## Rate Limiting

Rate limiting is configurable via environment variables:
- Default rate limit: 100 requests per hour per IP
- Chart generation may have stricter limits due to computational requirements
- Rate limit headers are included in all responses

## Security Considerations

- Authentication should be implemented by the integrating system
- HTTPS should be used in production
- API keys or tokens should be used for authentication
- Input validation is performed on all endpoints
- All analytics requests are logged for audit and monitoring