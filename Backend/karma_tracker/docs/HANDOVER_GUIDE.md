# KarmaChain Handover Guide

## System Overview

KarmaChain is a dual-ledger karma tracking system built with FastAPI and MongoDB. It provides a comprehensive API for tracking user actions, calculating karma/merit scores, and implementing progressive punishment and atonement mechanisms based on Vedic principles.

### System Architecture

**Core System Modules:**
1. **Karma Ledger Module** - Main karma tracking and calculation engine
2. **Atonement Engine** - Handles atonement plans and submissions
3. **Death Manager** - Processes user death events and loka assignments
4. **Appeal System** - Manages karma appeals and reviews
5. **Q-Learning Optimizer** - Optimizes karma calculations using reinforcement learning

### Core Handover Modules

1. **Data Module** - For analytics and research team (BHIV)
   - Contains data schemas, sample API responses, and analytics notes
   - Enables data-driven decision making and research
   - Includes Vedic corpus data for traditional karma classification

2. **System Module** - For infrastructure and deployment team (Unreal)
   - Contains Docker configuration, environment setup, and deployment notes
   - Enables portable and consistent deployment
   - Includes Windows batch scripts for local development

3. **Interface Module** - For external API team (Knowledgebase)
   - Contains API documentation, event payloads, and response codes
   - Enables seamless integration with external systems
   - Unified event gateway for simplified integration

## Local Development Setup

### Prerequisites
- Python 3.8+
- MongoDB 6.0+
- Docker and Docker Compose (recommended)
- Git
- Windows PowerShell (for Windows users)

### Quick Start Options

#### Option 1: Docker Compose (Recommended)
```bash
# Start all services (karma-api, mongo, mongo-express)
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs karma-api

# Stop services
docker-compose down
```

#### Option 2: Manual Setup
1. Clone the repository
2. Set up environment:
   ```bash
   # Linux/Mac
   chmod +x scripts/run_local.sh
   ./scripts/run_local.sh
   
   # Windows
   scripts\run_local.bat
   ```
3. The script will:
   - Create `.env` file from `.env.example`
   - Set up Python virtual environment
   - Install dependencies from `requirements.txt`
   - Check MongoDB connection
   - Start the FastAPI application
4. Access the API at http://localhost:8000
5. API documentation available at http://localhost:8000/docs
6. MongoDB admin interface at http://localhost:8081

### Service URLs
- **Karma API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MongoDB Admin**: http://localhost:8081 (admin/admin)
- **Health Check**: http://localhost:8000/health

## Departmental Ownership

### Analytics & Research Team (BHIV)
- **Ownership**: `/handover/data_module/`
- **Core Files**:
  - `data_schema.json` - Database schema definitions and field mappings
  - `sample_responses/` - Example API responses for all endpoints
  - `api_notes.md` - Notes on data collection points and analytics requirements
- **Project Files**:
  - `data/vedic_corpus/` - Traditional karma classification data
  - `schemas/token_schema.json` - Token validation schemas
  - `test_event_examples.json` - Test data for validation

### Infrastructure & Deployment Team (Unreal)
- **Ownership**: `/handover/system_module/`
- **Core Files**:
  - `Dockerfile` - Container definition and build instructions
  - `docker-compose.yml` - Multi-container orchestration
  - `env.example` - Environment variable template
  - `deployment_notes.md` - Deployment guidelines and best practices
- **Project Files**:
  - `docker-compose.yml` (root) - Production Docker configuration
  - `.env.example` - Complete environment configuration
  - `Dockerfile` (root) - Application container definition
  - `scripts/run_local.sh` - Linux/Mac development setup
  - `scripts/run_local.bat` - Windows development setup
  - `backups/` - Database backup storage
  - `logs/` - Application log storage
  - `uploads/` - Temporary file upload storage
  - `mongo-init/` - Database initialization scripts
- **New Integration**:
  - `/utils/unreal_broadcast.py` - WebSocket broadcast module for Unreal Engine
  - `/scripts/unreal_client_stub.py` - Sample Unreal client for testing
  - `/scripts/unreal_simulation.py` - 10-player simulation script

### External API Team (Knowledgebase)
- **Ownership**: `/handover/interface_module/`
- **Core Files**:
  - `api_map.md` - Complete API endpoint documentation
  - `event_payloads.md` - Request/response payload formats
  - `response_codes.md` - Error codes and troubleshooting
- **Project Files**:
  - `docs/api_documentation.md` - Additional API documentation
  - `test_*.py` files - API testing utilities
  - Unified event gateway documentation and examples

## System Modules Overview

### Core Application Modules

**Routes Structure (`/routes/v1/karma/`):**
- **log_action.py** - Karma action logging and processing
- **appeal.py** - Karma appeal submission and management
- **atonement.py** - Atonement plan generation and submission
- **death.py** - Death event processing and loka assignment
- **stats.py** - User statistics and karma calculations
- **event.py** - Unified event gateway for all operations

**Utility Modules (`/utils/`):**
- **atonement.py** - Atonement calculation algorithms
- **loka.py** - Loka assignment logic
- **merit.py** - Merit score calculations
- **paap.py** - Paap token generation and management
- **qlearning.py** - Q-learning optimization for karma calculations
- **tokens.py** - Token management and validation
- **transactions.py** - Transaction processing and logging
- **utils_user.py** - User utility functions

**Core Files:**
- **main.py** - FastAPI application entry point
- **models.py** - Database models and schemas
- **database.py** - MongoDB connection and operations
- **config.py** - Application configuration settings

## Integration Flow

### Traditional Endpoint Flow
The system supports a complete karma lifecycle:
1. **Log user actions** (`POST /v1/karma/log-action`)
2. **Submit appeals** for negative actions (`POST /v1/karma/appeal`)
3. **Request atonement plans** (`POST /v1/karma/atonement`)
4. **Submit atonement proof** (`POST /v1/karma/atonement/submit` or `POST /v1/karma/atonement/submit-with-file`)
5. **Record user death events** (`POST /v1/karma/death/event`)
6. **Retrieve user statistics** (`GET /v1/karma/stats/{user_id}`)

### Unified Event Gateway Flow
All operations can also be accessed through the unified event gateway:
- **Single endpoint**: `POST /v1/karma/event`
- **File uploads**: `POST /v1/karma/event/with-file`
- **Event types**: life_event, atonement, appeal, death_event, stats_request, atonement_with_file

### Karma Classification System
- **Minor Actions**: Small good/bad deeds (helping neighbor, white lies)
- **Medium Actions**: Significant deeds (charity, disrespect)
- **Major Actions**: Serious deeds (teaching dharma, grave harm)
- **Maha Actions**: Extreme deeds (spiritual guidance, heinous crimes)

### Atonement Mechanisms
- **Jap**: Mantra repetition (108, 540, 1080 repetitions)
- **Tap**: Fasting and self-discipline (3, 7, 14 days)
- **Bhakti**: Devotional acts (1, 3, 7 acts)
- **Daan**: Charitable giving (5%, 10%, 20% of income)

## Unreal Engine Integration

### WebSocket Broadcast System
The KarmaChain system includes a WebSocket broadcast module (`/utils/unreal_broadcast.py`) that enables real-time communication with Unreal Engine clients.

**Key Features:**
- Real-time karmic event broadcasting
- Support for multiple event types (life events, death events, rebirth, feedback signals, analytics)
- Client subscription management
- Priority-based event queuing

### Event Types Broadcasted
1. **Life Events** - User actions and their karmic impact
2. **Death Events** - User death with loka assignment
3. **Rebirth Events** - User rebirth with karma inheritance
4. **Feedback Signals** - Net karmic influence metrics
5. **Analytics Events** - Trend data and engagement metrics

### Integration Flow Diagram
```
graph TD
    A[KarmaChain Core] --> B[Unreal Broadcast Module]
    B --> C[WebSocket Server]
    C --> D[Unreal Engine Client 1]
    C --> E[Unreal Engine Client 2]
    C --> F[Unreal Engine Client N]
    
    G[Life Event] --> A
    H[Death Event] --> A
    I[Rebirth Event] --> A
    J[Feedback Signal] --> A
    K[Analytics Data] --> A
    
    A --> L[Broadcast to All Clients]
```

### Client Connection Process
1. Unreal client connects to WebSocket server at `ws://localhost:8765/{client_id}`
2. Server registers client and sends welcome message
3. Client can subscribe to specific event types
4. Server broadcasts relevant events to subscribed clients
5. Client processes events and updates visualization

### Testing the Integration
To test the Unreal Engine integration:

```bash
# Run the 10-player simulation
python scripts/unreal_simulation.py

# Run the sample Unreal client stub
python scripts/unreal_client_stub.py
```

## Deployment Instructions

### Production Deployment
1. **Environment Setup**:
   ```bash
   # Copy and configure environment variables
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Docker Deployment**:
   ```bash
   # Build and start all services
   docker-compose up -d
   
   # Verify services are running
   docker-compose ps
   
   # Check logs
   docker-compose logs karma-api
   ```

3. **Manual Deployment**:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Start the application
   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Key Configuration Parameters
- **MongoDB Connection**: Set `MONGO_URI` in `.env`
- **API Port**: Default is 8000, configurable via `PORT`
- **WebSocket Port**: Default is 8765 for Unreal integration
- **Secret Key**: Set `SECRET_KEY` for security
- **Debug Mode**: Set `DEBUG=False` for production

### Monitoring and Maintenance
- **Health Checks**: Access `/health` endpoint
- **Metrics**: Access `/metrics` for Prometheus metrics
- **Logs**: Check `logs/` directory for application logs
- **Backups**: Regular MongoDB backups in `backups/` directory

## Testing & Quality Assurance

### Test Suite Structure
- **Unit Tests**: Individual component testing in `tests/` directory
- **Integration Tests**: End-to-end workflow testing
- **Comprehensive Demo**: Full karma lifecycle testing in `tests/integration_demo.py`
- **Test Runner**: Automated test execution with `test_runner.py`

### Test Coverage
- ✅ Karma action logging (positive/negative actions)
- ✅ Appeal submission and processing
- ✅ Atonement plan generation and completion
- ✅ Death event recording and Paap token handling
- ✅ User statistics and karma calculation
- ✅ Error handling for invalid inputs
- ✅ Unified event gateway functionality
- ✅ File upload with atonement submissions
- ✅ Event routing and processing
- ✅ Database integration and persistence
- ✅ Event retention and cleanup policies
- ✅ Docker environment testing

## Handover Status

### ✅ Ready for Handover - COMPLETED

**Core System Components:**
- ✅ **Versioned API structure** (`/v1/karma/`) - All endpoints operational
- ✅ **Unified event endpoint** (`/v1/karma/event`) - Full implementation with file upload support
- ✅ **Docker configuration** with Windows batch support and comprehensive environment setup
- ✅ **Complete documentation** - API maps, event payloads, response codes updated for unified system
- ✅ **Integration test suite** with pytest and comprehensive test coverage
- ✅ **Windows development environment** setup with PowerShell support
- ✅ **MongoDB connection validation** with authentication and backup systems
- ✅ **Vedic karma classification system** with traditional atonement mechanisms
- ✅ **File upload system** with validation, storage, and cleanup
- ✅ **Event retention and cleanup** with configurable policies
- ✅ **Database collections** properly configured (karma_events, users, atonement_files, merit_transactions)
- ✅ **Environment configuration** complete with all unified event system variables
- ✅ **Event audit trail** - Complete event logging and storage system
- ✅ **Event processing** - Automatic routing and processing with status tracking
- ✅ **File upload validation** - Comprehensive file type and size validation
- ✅ **Temporary file storage** - Automatic cleanup and retention policies
- ✅ **Docker environment testing** - Complete containerized testing environment
- ✅ **Unified event gateway** - Single endpoint for all operations with file support

**Documentation Status:**
- ✅ **Interface Module** (`/handover/interface_module/`) - COMPLETE
  - `api_map.md` - Updated with unified event endpoints and file upload
  - `event_payloads.md` - Updated with unified event request/response models
  - `response_codes.md` - Updated with unified event error codes (K017-K021)

- ✅ **System Module** (`/handover/system_module/`) - COMPLETE
  - Docker configuration enhanced with file upload volumes
  - Environment variables updated for unified event system
  - Backup and retention policies configured

- ✅ **Data Module** (`/handover/data_module/`) - COMPLETE
  - Data schemas updated for unified event storage
  - Sample responses include file upload examples

### ⏳ Pending Items - FUTURE ENHANCEMENTS

**Security & Authentication:**
- ⏳ Authentication implementation (currently in development mode)
- ⏳ Rate limiting and API throttling (framework ready, needs activation)
- ⏳ Advanced security headers and CORS configuration
- ⏳ File upload security enhancements (virus scanning, content validation)
- ⏳ Event encryption for sensitive data

**Production Features:**
- ⏳ Advanced monitoring and logging with metrics collection
- ⏳ Production deployment pipeline with CI/CD integration
- ⏳ Load balancing and horizontal scaling configuration
- ⏳ Event streaming and real-time processing
- ⏳ Advanced backup and disaster recovery

**Additional Modules:**
- ⏳ User and Admin modules (commented out in current build)
- ⏳ Advanced analytics dashboard with real-time metrics
- ⏳ Notification system for atonement reminders
- ⏳ Event replay and audit capabilities
- ⏳ Advanced search and filtering for events

**Performance Optimization:**
- ⏳ Database indexing optimization for large datasets
- ⏳ Caching layer for frequently accessed data
- ⏳ Background job processing for cleanup tasks
- ⏳ Event batch processing for high-volume scenarios
- ⏳ Database sharding for event storage

## API Endpoints Summary

### Primary Karma Endpoints
| Endpoint | Method | Description |
|----------|---------|-------------|
| `/v1/karma/log-action` | POST | Log user karma actions |
| `/v1/karma/appeal` | POST | Submit appeals for negative actions |
| `/v1/karma/appeal/{appeal_id}` | GET | Get appeal status by ID |
| `/v1/karma/atonement` | POST | Request atonement plans |
| `/v1/karma/atonement/submit-atonement` | POST | Submit atonement proof (text) |
| `/v1/karma/atonement/submit-atonement-with-file` | POST | Submit atonement proof with file |
| `/v1/karma/atonement/{user_id}` | GET | Get user atonement plans |
| `/v1/karma/death` | POST | Record user death events |
| `/v1/karma/stats/{user_id}` | GET | Retrieve user statistics |

### Unified Event Gateway
| Endpoint | Method | Description |
|----------|---------|-------------|
| `/v1/karma/event` | POST | Unified event gateway (all operations) |
| `/v1/karma/event/with-file` | POST | File-based event submissions |

### System Endpoints
| Endpoint | Method | Description |
|----------|---------|-------------|
| `/health` | GET | Health check endpoint |
| `/metrics` | GET | Prometheus metrics endpoint |

## Support

For questions or issues, please contact the KarmaChain development team.

### Key Files Reference
- **Main Application**: `main.py`
- **API Routes**: `routes/v1/karma/` - All karma-related endpoints
- **Database Models**: `models.py` - MongoDB schemas and models
- **Configuration**: `config.py` - Application settings and environment
- **Test Suite**: `tests/` and `test_runner.py` - Comprehensive testing
- **Setup Scripts**: `scripts/run_local.sh` and `scripts/run_local.bat`
- **Docker Configuration**: `docker-compose.yml` and `Dockerfile`
- **Environment Template**: `.env.example` - Complete configuration template

### Environment Variables
**Database Configuration:**
- `MONGO_URI`: MongoDB connection string
- `DB_NAME`: Database name (default: "karmachain")
- `MONGO_INITDB_ROOT_USERNAME`: MongoDB admin username
- `MONGO_INITDB_ROOT_PASSWORD`: MongoDB admin password
- `MONGO_HOST`: MongoDB host (default: "mongo")
- `MONGO_PORT`: MongoDB port (default: 27017)
- `MONGO_DB`: Database name (default: "karmachain")

**Application Settings:**
- `SECRET_KEY`: Application secret key for security
- `DEBUG`: Debug mode flag (True/False)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)
- `API_VERSION`: API version (default: "v1")
- `APP_NAME`: Application name (default: "KarmaChain")

**File Upload Configuration:**
- `MAX_FILE_SIZE`: Maximum file upload size (bytes)
- `UPLOAD_DIR`: Directory for temporary file storage
- `ALLOWED_FILE_TYPES`: Comma-separated list of allowed file extensions
- `FILE_UPLOAD_TIMEOUT`: Upload timeout in seconds
- `UPLOAD_RETENTION_HOURS`: How long to keep uploaded files (hours)

**Event Processing:**
- `EVENT_RETENTION_DAYS`: How long to keep events (days)
- `EVENT_CLEANUP_INTERVAL`: Cleanup interval in seconds
- `EVENT_ROUTING_TIMEOUT`: Event routing timeout (seconds)
- `MAX_EVENTS_PER_BATCH`: Maximum events to process per batch

**Q-Learning Parameters:**
- `ALPHA`: Learning rate (default: 0.15)
- `GAMMA`: Discount factor (default: 0.9)
- `EPSILON`: Exploration rate (default: 0.2)

**Docker Configuration:**
- `COMPOSE_PROJECT_NAME`: Docker Compose project name
- `MONGO_EXPRESS_PORT`: MongoDB Express port (default: 8081)
- `API_PORT`: API server port (default: 8000)

**Security Settings:**
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)
- `RATE_LIMIT_PER_MINUTE`: API rate limit per minute
- `FILE_UPLOAD_RATE_LIMIT`: File upload rate limit per hour