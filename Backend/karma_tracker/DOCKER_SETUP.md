# KarmaChain Docker Setup Guide

This guide provides comprehensive instructions for running KarmaChain using Docker Compose, including setup, configuration, and troubleshooting.

## Overview

The Docker setup includes:
- **karma-api**: FastAPI application serving the KarmaChain API
- **mongo**: MongoDB database for data persistence
- **mongo-express**: Web-based MongoDB admin interface

## Quick Start

### Prerequisites

1. **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
2. **Docker Compose** (included with Docker Desktop)
3. **curl** (for health checks)

### Windows Setup

1. Open PowerShell or Command Prompt as Administrator
2. Navigate to the project directory:
   ```cmd
   cd C:\path\to\karma-chain-Q
   ```
3. Run the setup script:
   ```cmd
   scripts\run_local.bat
   ```

### Linux/Mac Setup

1. Open terminal
2. Navigate to the project directory:
   ```bash
   cd /path/to/karma-chain-Q
   ```
3. Make the script executable:
   ```bash
   chmod +x scripts/run_local.sh
   ```
4. Run the setup script:
   ```bash
   ./scripts/run_local.sh
   ```

## Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Environment Configuration

Create a `.env` file from the example:
```bash
cp .env.example .env
```

Update the `.env` file with your configuration:
```env
# MongoDB Configuration
MONGODB_URI=mongodb://mongo:27017/karmachain
DATABASE_NAME=karmachain

# Application Configuration
SECRET_KEY=your-secret-key-here
DEBUG=true

# API Configuration
API_VERSION=v1
KARMA_BASE_URL=http://localhost:8000/v1/karma

# Unified Event System Configuration
MAX_FILE_SIZE=1048576  # 1MB for file uploads
EVENT_RETENTION_DAYS=90  # Keep events for 90 days
EVENT_CLEANUP_INTERVAL=86400  # Daily cleanup in seconds

# File Upload Configuration
UPLOAD_DIR=./uploads
ALLOWED_FILE_TYPES=pdf,jpg,jpeg,png,txt
FILE_UPLOAD_TIMEOUT=30
```

### 2. Start Services

Build and start all services:
```bash
docker-compose up -d --build
```

### 3. Verify Setup

Check service health:
```bash
# Check API health
curl http://localhost:8000/health

# Check MongoDB connection
docker-compose exec mongo mongosh --eval "db.adminCommand('ping')"
```

### Quick Start Commands

Once configured, use these commands for daily operations:

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs in real-time
docker-compose logs -f

# Stop all services
docker-compose down

# Restart services
docker-compose restart
```

## Service Information

### Available Services

| Service | URL | Description |
|---------|-----|-------------|
| Karma API | http://localhost:8000 | Main API endpoint with unified event system |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| MongoDB | localhost:27017 | Database connection |
| Mongo Express | http://localhost:8081 | Database admin interface |

### Default Credentials

- **Mongo Express**: 
  - Username: `admin`
  - Password: `admin` (change in docker-compose.yml)

### Service Features

#### karma-api (FastAPI Application)
- **Port**: 8000
- **Purpose**: Main API server for KarmaChain with unified event gateway
- **Health Check**: Available at `http://localhost:8000/health`
- **Features**: 
  - Unified event system for all karma operations
  - File upload support with validation
  - Comprehensive event logging and audit trail
  - Configurable event retention and cleanup

#### mongo (MongoDB Database)
- **Port**: 27017
- **Purpose**: Primary database for storing karma events and user data
- **Authentication**: Enabled with root and application-specific users
- **Features**: 
  - WiredTiger storage engine with optimized cache
  - Automatic backups support
  - Health monitoring and connection pooling

#### mongo-express (Database Admin Interface)
- **Port**: 8081
- **Purpose**: Web-based MongoDB administration interface
- **Access**: `http://localhost:8081`
- **Credentials**: admin/admin (change in production)

## Docker Compose Configuration

### Services Overview

#### karma-api
- **Build**: Uses Dockerfile in project root
- **Ports**: 8000:8000
- **Environment**: Loads from .env file with unified event system configuration
- **Dependencies**: mongo
- **Volumes**: Application code, logs, file uploads
- **Features**: Unified event gateway, file upload support, event retention

#### mongo
- **Image**: mongo:6.0
- **Ports**: 27017:27017
- **Volumes**: mongo_data for persistence, backups directory
- **Environment**: Database initialization with authentication
- **Features**: WiredTiger cache optimization, health monitoring

#### mongo-express
- **Image**: mongo-express:latest
- **Ports**: 8081:8081
- **Dependencies**: mongo
- **Environment**: Admin credentials
- **Purpose**: Database administration interface

### Network Configuration

All services communicate through the `karma-network` bridge network.

## Unified Event System Features

The Docker setup includes a comprehensive unified event system with the following capabilities:

### Event Gateway
- **Single Endpoint**: `/v1/karma/unified_event` for all karma operations
- **Event Types**: life_event, atonement, appeal, death_event, stats_request
- **Automatic Logging**: All events stored in karma_events collection
- **Event Routing**: Intelligent routing to appropriate internal endpoints

### File Upload Support
- **Endpoint**: `/v1/karma/unified_event_with_file` for file-based atonement
- **File Validation**: Type, size, and content validation
- **Temporary Storage**: Files stored in `./uploads` directory
- **Automatic Cleanup**: Old files removed based on retention policy
- **Supported Types**: pdf, jpg, jpeg, png, txt
- **Size Limit**: 1MB (configurable via MAX_FILE_SIZE)

### Event Retention and Cleanup
- **Retention Period**: 90 days (configurable via EVENT_RETENTION_DAYS)
- **Cleanup Interval**: Daily cleanup (configurable via EVENT_CLEANUP_INTERVAL)
- **Audit Trail**: Complete event history maintained for compliance
- **Storage Optimization**: Automatic cleanup of old events and files

### Database Collections
- **karma_events**: Stores all unified events with full audit trail
- **users**: User data and karma scores
- **atonement_files**: File upload metadata and references
- **merit_transactions**: Merit score transactions

## Development Workflow

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f karma-api
docker-compose logs -f mongo
```

### Running Tests

```bash
# Run integration tests
docker-compose exec karma-api python tests/integration_demo.py

# Run all tests
docker-compose exec karma-api python test_runner.py

# Run pytest
docker-compose exec karma-api pytest

# Test unified event system
docker-compose exec karma-api python test_unified_event_with_db.py

# Test file upload functionality
docker-compose exec karma-api python test_atonement_storage.py

# Test event endpoints
docker-compose exec karma-api python test_event_endpoint.py
```

### Database Management

```bash
# Access MongoDB shell
docker-compose exec mongo mongosh karmachain

# Backup database
docker-compose exec mongo mongodump --db karmachain --out /backup

# Restore database
docker-compose exec mongo mongorestore --db karmachain /backup/karmachain
```

### Rebuilding Services

```bash
# Rebuild specific service
docker-compose build karma-api

# Rebuild and restart all services
docker-compose down
docker-compose up -d --build
```

## Troubleshooting

### Common Issues

#### Port Conflicts
If ports 8000, 27017, or 8081 are already in use:
1. Stop conflicting services
2. Or modify ports in docker-compose.yml

#### Docker Not Running
Ensure Docker Desktop is running and the Docker daemon is active.

#### Permission Issues (Linux/Mac)
```bash
sudo chown -R $USER:$USER .
chmod +x scripts/run_local.sh
```

#### MongoDB Connection Issues
1. Check MongoDB logs: `docker-compose logs mongo`
2. Verify network connectivity: `docker network ls`
3. Check if mongo-express can connect: `http://localhost:8081`

#### File Upload Issues
1. **Check file size limits**: Verify MAX_FILE_SIZE in environment
2. **Check supported file types**: Ensure file extension is allowed
3. **Check upload directory permissions**: Verify ./uploads directory exists
4. **Check file upload timeout**: Adjust FILE_UPLOAD_TIMEOUT if needed
5. **Check disk space**: Ensure sufficient space for file uploads
6. **Check file upload logs**: `docker-compose logs karma-api | grep -i upload`

#### Event Processing Issues
1. **Check event type validation**: Ensure correct event_type parameter
2. **Check event data format**: Verify JSON structure matches requirements
3. **Check karma_events collection**: `docker-compose exec mongo mongosh karmachain --eval "db.karma_events.find().limit(5)"`
4. **Check event routing**: Look for routing errors in logs
5. **Check event retention**: Verify EVENT_RETENTION_DAYS setting

### Health Checks

The setup script includes automatic health checks. Manual checks:

```bash
# API Health
curl http://localhost:8000/health

# MongoDB Health
docker-compose exec mongo mongosh --eval "db.runCommand('ping')"

# Service Status
docker-compose ps
```

### Logs and Debugging

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs karma-api
docker-compose logs mongo

# View recent logs only
docker-compose logs --tail=100
```

## Performance Optimization

### Resource Limits

Add resource limits to docker-compose.yml:
```yaml
services:
  karma-api:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### Volume Management

Clean up unused volumes:
```bash
docker volume prune
```

### Image Optimization

Use multi-stage builds in Dockerfile for smaller images.

## Security Considerations

### Production Deployment

1. **Change default passwords** in docker-compose.yml
2. **Use environment variables** for sensitive data
3. **Enable HTTPS** with reverse proxy (nginx/traefik)
4. **Set up firewall rules** for exposed ports
5. **Regular security updates** for base images

### Environment Variables

Never commit sensitive data to version control. Use:
- Docker secrets (Swarm mode)
- External secret management (HashiCorp Vault, AWS Secrets Manager)
- Environment files (.env) excluded from git

## Advanced Configuration

### Custom MongoDB Configuration

Create `mongo-init/custom-config.js`:
```javascript
// Custom MongoDB configuration
db.setProfilingLevel(1, { slowms: 100 });
db.adminCommand({ setParameter: 1, maxConns: 200 });
```

### Multiple Environments

Create separate compose files:
- `docker-compose.dev.yml`
- `docker-compose.prod.yml`
- `docker-compose.test.yml`

Use with: `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up`

### Monitoring

Add monitoring services:
```yaml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

## Cleanup

### Stop Services
```bash
docker-compose down
```

### Remove Everything
```bash
docker-compose down -v --remove-orphans
docker system prune -a
```

### Keep Data
```bash
docker-compose down  # Keeps volumes
docker-compose up -d  # Restart with existing data
```

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review service logs: `docker-compose logs`
3. Check Docker status: `docker system info`
4. Verify network connectivity: `docker network inspect karma-network`

## Next Steps

Once your Docker environment is running:
1. Test the API endpoints at http://localhost:8000/docs
2. Run the integration demo: `docker-compose exec karma-api python tests/integration_demo.py`
3. Explore the database using Mongo Express at http://localhost:8081
4. Review the API documentation in `docs/api_documentation.md`