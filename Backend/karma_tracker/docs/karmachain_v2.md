# KarmaChain v2: Vedic-Based Dual-Ledger Karmic Engine

## Overview

KarmaChain v2 is a comprehensive Vedic-based karma tracking system that implements a dual-ledger approach tracking both positive (Punya) and negative (Paap) karmic actions. Built with FastAPI and MongoDB, it provides a complete karma lifecycle management system with progressive atonement mechanisms based on traditional Vedic principles.

### Key Enhancements
- **Vedic Classification System**: Four-tier karma classification (Minor, Medium, Major, Maha)
- **Progressive Atonement**: Jap, Tap, Bhakti, and Daan mechanisms
- **Comprehensive Testing**: Full integration test suite with pytest
- **Cross-Platform Support**: Windows batch scripts and Linux/Mac shell scripts
- **Unified Event Gateway**: Single endpoint for all karma operations with file upload support
- **Event Audit Trail**: Complete event logging and storage system
- **Docker Environment**: Complete containerized deployment with MongoDB

## Core Concepts

### Dual-Ledger System

The dual-ledger system maintains two separate token categories:

1. **Positive Tokens (Existing)**
   - DharmaPoints
   - SevaPoints
   - PunyaTokens (minor, medium, major)

2. **Negative Tokens (New)**
   - PaapTokens (minor, medium, maha)

### Paap Classification

Actions that generate negative karma are classified into four severity levels based on Vedic principles:

- **Minor Paap**: Small transgressions (e.g., false speech, breaking promises, minor disrespect)
- **Medium Paap**: Moderate transgressions (e.g., cheating, disrespecting teachers, gossip)
- **Major Paap**: Serious transgressions (e.g., causing significant harm, grave disrespect)
- **Maha Paap**: Severe transgressions (e.g., violence, causing serious harm, spiritual transgressions)

### Atonement System

Users can atone for negative actions through four types of Vedic practices with progressive requirements based on severity:

1. **Jap**: Recitation of mantras or prayers
   - Minor: 108 repetitions
   - Medium: 540 repetitions  
   - Major: 1080 repetitions
   - Maha: 1080+ repetitions

2. **Tap**: Austerities like fasting
   - Minor: 3 days of fasting/self-discipline
   - Medium: 7 days of fasting/self-discipline
   - Major: 14 days of fasting/self-discipline
   - Maha: 21+ days of fasting/self-discipline

3. **Bhakti**: Devotional practices
   - Minor: 1 devotional act (temple visit, prayer, service)
   - Medium: 3 devotional acts
   - Major: 7 devotional acts
   - Maha: 7+ devotional acts

4. **Daan**: Charitable giving
   - Minor: 5% of income to charity
   - Medium: 10% of income to charity
   - Major: 20% of income to charity
   - Maha: 20%+ of income to charity

### Rebirth Mechanics

When a user completes their current lifecycle (death event), their karma determines their rebirth destination:

- **Swarga**: Heavenly realm for those with excellent karma
- **Martya**: Middle realm (human world) for those with balanced karma
- **Naraka**: Lower realm for those with predominantly negative karma

## API Endpoints

### Current Implementation (v1/karma)

The system now uses a versioned API structure under `/v1/karma/`:

#### Primary Karma Endpoints
- `POST /v1/karma/log-action` - Log karma actions
- `POST /v1/karma/appeal` - Submit appeals
- `POST /v1/karma/atonement` - Request atonement plans
- `POST /v1/karma/atonement/submit-atonement` - Submit atonement proof
- `POST /v1/karma/atonement/submit-atonement-with-file` - Submit atonement with file proof
- `GET /v1/karma/appeal/{appeal_id}` - Get appeal status
- `POST /v1/karma/death` - Record death events
- `GET /v1/karma/stats/{user_id}` - Get user statistics

#### Unified Event Gateway
- `POST /v1/karma/event` - Unified event gateway (all operations)
- `POST /v1/karma/event/with-file` - File-based event submissions

#### System Endpoints
- `GET /health` - Health check
- `GET /metrics` - Prometheus-compatible metrics

### Unified Event Gateway

The unified event gateway provides a single entry point for all karma operations with automatic event logging and audit trail.

#### POST /v1/karma/event
Process any karma-related event through the unified gateway.

**Supported Event Types:**
- **life_event**: Log user actions (maps to `/log-action`)
- **atonement**: Submit atonement proof (maps to `/atonement/submit`)
- **atonement_with_file**: Submit atonement with file upload (maps to `/atonement/submit-with-file`)
- **appeal**: Request karma appeal (maps to `/appeal`)
- **death_event**: Process user death events (maps to `/death/event`)
- **stats_request**: Get user statistics (maps to `/stats/{user_id}`)

**Request Structure:**
```json
{
  "type": "string",
  "data": {},
  "timestamp": "ISO 8601 datetime",
  "source": "string"
}
```

**Response includes routing information:**
```json
{
  "status": "success",
  "event_type": "string",
  "message": "string",
  "data": {},
  "timestamp": "datetime",
  "routing_info": {
    "internal_endpoint": "string",
    "mapped_from": "string"
  }
}
```

#### File Upload Support

#### POST /v1/karma/event/with-file
Submit events with file attachments, supporting atonement submissions with proof files.

**File Upload Requirements:**
- Maximum file size: 1MB (configurable via `MAX_FILE_SIZE`)
- Supported file types: pdf, jpg, jpeg, png, txt
- Files stored temporarily with automatic cleanup
- Upload timeout: 30 seconds (configurable via `FILE_UPLOAD_TIMEOUT`)

### Appeal System

#### POST /v1/karma/appeal
Submit an appeal for a negative action.

**Request Body:**
```json
{
  "user_id": "string",
  "action": "string",
  "note": "string"
}
```

**Response:**
```json
{
  "appeal_id": "string",
  "status": "pending",
  "atonement_plan_id": "string"
}
```

#### GET /v1/karma/appeal/{appeal_id}
Get the status and details of a specific appeal.

#### POST /v1/karma/atonement/submit-atonement
Submit proof of atonement activities.

**Request Body:**
```json
{
  "user_id": "string",
  "atonement_plan_id": "string",
  "atonement_type": "string",
  "proof": "string",
  "units": "number"
}
```

**Response:**
```json
{
  "status": "string",
  "progress": {
    "Jap": "number",
    "Tap": "number",
    "Bhakti": "number",
    "Daan": "number"
  },
  "completed": "boolean"
}
```

#### POST /v1/karma/atonement/submit-atonement-with-file
Submit proof of atonement with file upload support.

#### POST /v1/karma/death
Trigger a death event for rebirth processing.

**Request Body:**
```json
{
  "user_id": "string"
}
```

**Response:**
```json
{
  "assigned_loka": "string",
  "net_karma": "number",
  "carryover": {
    "carryover_paap": "number",
    "carryover_punya": "number",
    "starting_level": "string"
  }
}
```

### Updated Actions API

The existing `/actions/log` endpoint now supports Paap-generating actions:

**Response includes:**
```json
{
  "paap_severity": "string",
  "paap_tokens": {
    "minor": "number",
    "medium": "number",
    "maha": "number"
  },
  "atonement_plan_id": "string (optional)"
}
```

## Implementation Details

### Token Schema

The token schema is defined in `schemas/token_schema.json` and includes:

- Existing tokens (DharmaPoints, SevaPoints, PunyaTokens)
- New PaapTokens with severity classes
- Atonement credits (Jap, Tap, Bhakti, Daan)

### Configuration

New constants in `config.py`:

- `PaapTokens`: Definition of negative token types
- `PAAP_CLASSES`: Classification of actions by severity
- `PRAYASCHITTA_MAP`: Atonement requirements for each severity level
- `LOKA_THRESHOLDS`: Thresholds for rebirth assignment

### Utility Modules

1. **utils/paap.py**
   - Classifies actions into Paap severity categories
   - Calculates Paap values based on severity
   - Applies PaapTokens to user balances
   - Calculates total weighted Paap score

2. **utils/atonement.py**
   - Retrieves prescribed atonement plans
   - Creates new atonement plans
   - Validates and records atonement proofs
   - Updates atonement progress
   - Marks plans as completed
   - Reduces PaapTokens upon successful atonement

3. **utils/loka.py**
   - Calculates net karma (Punya vs Paap)
   - Assigns users to appropriate Loka
   - Creates rebirth carryover objects
   - Applies rebirth effects

4. **utils/qlearning.py** (Enhanced)
   - Added support for atonement rewards
   - Q-learning steps for atonement completion

### Event Storage and Audit System

The unified event system includes comprehensive event logging and storage:

#### Event Collections
- **karma_events**: Stores all events processed through the unified gateway
- **atonement_files**: Stores metadata for file uploads
- **merit_transactions**: Records all karma transactions
- **users**: User profiles with karma balances

#### Event Processing Features
- **Automatic Logging**: All events are logged with complete request/response data
- **Event Status Tracking**: Track events from pending → processed/failed
- **Error Logging**: Detailed error information for debugging
- **Performance Monitoring**: Event processing time and success rates
- **File Upload Integration**: Temporary file storage with automatic cleanup
- **Retention Policies**: Configurable event cleanup (default: 90 days)

#### File Upload System
- **Validation**: File type, size, and content validation
- **Storage**: Temporary storage in `./uploads` directory
- **Cleanup**: Automatic removal of old files based on retention policy
- **Security**: File type restrictions and size limits
- **Integration**: Seamless integration with atonement submissions

### Vedic Dataset

The system includes a dataset of Vedic references in `data/vedic_corpus/`:

- `mahapaap_map.json`: Maps actions to severity classes with textual references
- `sources.md`: Documentation of Vedic sources

## Migration

To migrate from KarmaChain v1 to v2:

1. Run the migration script: `python scripts/migrate_to_v2.py`
2. The script will:
   - Create new collections for appeals and atonements
   - Update user schema to include PaapTokens
   - Create necessary indexes
   - Initialize default values



### Test Coverage
- ✅ Karma action logging (positive/negative actions)
- ✅ Appeal submission and processing
- ✅ Atonement plan generation and completion
- ✅ Death event recording and Paap token handling
- ✅ User statistics and karma calculation
- ✅ Error handling for invalid inputs
- ✅ Unified event gateway functionality

## Security Considerations

1. **Validation**: All user inputs are validated before processing
2. **Authentication**: Ensure proper authentication for all endpoints (currently not implemented)
3. **File Uploads**: Atonement proof file uploads are validated for type and size
4. **Data Integrity**: Transactions are atomic to prevent partial updates
5. **HTTPS**: Use HTTPS in production environments
6. **Rate Limiting**: Implement rate limiting for production deployments

## Development Setup

### Quick Start
```bash
# Windows
scripts\run_local.bat

# Linux/Mac
chmod +x scripts/run_local.sh
./scripts/run_local.sh
```

### Manual Setup
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

### Environment Variables
- `MONGODB_URI`: MongoDB connection string
- `DATABASE_NAME`: Database name (default: "karmachain")
- `SECRET_KEY`: Application secret key
- `DEBUG`: Debug mode flag

## Current Implementation Status

### ✅ Implemented Features
- **Vedic Classification System**: Four-tier karma classification with traditional Vedic principles
- **Dual-Ledger System**: Complete Punya/Paap token tracking
- **Progressive Atonement**: Jap, Tap, Bhakti, Daan mechanisms with severity-based requirements
- **Versioned API**: `/v1/karma/` endpoints with unified event gateway
- **Unified Event Gateway**: Single endpoint for all operations with file upload support
- **File Upload System**: Secure file upload with validation, storage, and cleanup
- **Event Audit Trail**: Complete event logging and storage system
- **Docker Environment**: Complete containerized deployment with MongoDB
- **Comprehensive Testing**: Full test suite with integration demos
- **Cross-Platform Support**: Windows batch scripts and Linux/Mac shell scripts
- **Health Monitoring**: Health check endpoint for system status
- **Event Retention Policies**: Configurable cleanup and retention
- **Database Collections**: Properly configured MongoDB collections with indexes

### ⏳ Pending Features
- **User/Admin Modules**: Currently commented out in main.py (modules don't exist yet)
- **Authentication System**: To be implemented by integrating systems
- **Rate Limiting**: Recommended for production deployments
- **Advanced Monitoring**: Production-grade logging and monitoring
- **Production Deployment**: Complete CI/CD pipeline

### 🚫 Deprecated Features
- **Old Appeal Endpoints**: `/appeal/*` endpoints replaced with `/v1/karma/*`
- **Legacy Action Logging**: Replaced with Vedic-classified action system
- **Basic Atonement**: Enhanced with progressive Vedic atonement mechanisms
- **Individual Action Endpoints**: Replaced by unified event gateway
- **Direct Database Access**: All operations go through API layer
- **Legacy Appeal System**: Replaced by new appeal submission process
- **Manual File Handling**: File uploads now handled through unified event system