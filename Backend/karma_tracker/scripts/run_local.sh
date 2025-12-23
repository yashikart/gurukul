#!/bin/bash

# KarmaChain Local Development Setup Script
# This script sets up the complete KarmaChain development environment with Docker

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Docker is running
check_docker() {
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker service."
        exit 1
    fi
    
    print_success "Docker is installed and running"
}

# Function to check if Docker Compose is available
check_docker_compose() {
    if command_exists docker-compose; then
        DOCKER_COMPOSE="docker-compose"
    elif docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
    else
        print_error "Docker Compose is not installed. Please install Docker Compose."
        exit 1
    fi
    
    print_success "Docker Compose is available: $DOCKER_COMPOSE"
}

# Function to create environment file
create_env_file() {
    if [ ! -f .env ]; then
        print_status "Creating .env file..."
        cat > .env << 'EOF'
# MongoDB Configuration
MONGO_URI=mongodb://mongo:27017/karmachain
MONGO_HOST=mongo
MONGO_PORT=27017
MONGO_DB=karmachain

# Application Configuration
API_VERSION=v1
APP_NAME=KarmaChain
DEBUG=true

# File Upload Configuration
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./uploads
ALLOWED_FILE_TYPES=jpg,jpeg,png,pdf,doc,docx
FILE_RETENTION_HOURS=24

# Event Processing Configuration
EVENT_PROCESSING_TIMEOUT=30
EVENT_BATCH_SIZE=100

# Docker Configuration
COMPOSE_PROJECT_NAME=karmachain
MONGO_EXPRESS_PORT=8081
API_PORT=8000

# Security
CORS_ORIGINS=*
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
FILE_UPLOAD_RATE_LIMIT=10
EOF
        
        # Generate a random secret key
        SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || date | md5sum | head -c 32)
        echo "SECRET_KEY=$SECRET_KEY" >> .env
        
        print_success "Created .env file with unified event system support"
    else
        print_warning ".env file already exists, skipping creation"
    fi
}

# Function to create directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p logs mongo-init uploads backups
    print_success "Created directories"
}

# Function to create MongoDB initialization script
create_mongo_init() {
    if [ ! -f mongo-init/init-mongo.js ]; then
        print_status "Creating MongoDB initialization script..."
        cat > mongo-init/init-mongo.js << 'EOF'
// Initialize KarmaChain database
db = db.getSiblingDB('karmachain');

// Create collections
db.createCollection('users');
db.createCollection('actions');
db.createCollection('transactions');
db.createCollection('appeals');
db.createCollection('atonements');
db.createCollection('deaths');
db.createCollection('karma_events');
db.createCollection('atonement_files');
db.createCollection('merit_transactions');

// Create indexes
db.users.createIndex({ "user_id": 1 }, { unique: true });
db.actions.createIndex({ "user_id": 1, "timestamp": -1 });
db.transactions.createIndex({ "user_id": 1, "timestamp": -1 });
db.appeals.createIndex({ "user_id": 1, "status": 1 });
db.atonements.createIndex({ "user_id": 1, "status": 1 });
db.karma_events.createIndex({ "event_id": 1 }, { unique: true });
db.karma_events.createIndex({ "user_id": 1, "event_type": 1, "timestamp": -1 });
db.atonement_files.createIndex({ "file_id": 1 }, { unique: true });
db.atonement_files.createIndex({ "user_id": 1, "upload_timestamp": -1 });
db.merit_transactions.createIndex({ "user_id": 1, "timestamp": -1 });

print('KarmaChain database initialized successfully with unified event system');
EOF
        print_success "Created MongoDB initialization script with unified event system support"
    fi
}

# Function to pull Docker images
pull_images() {
    print_status "Pulling Docker images..."
    $DOCKER_COMPOSE pull
    print_success "Docker images pulled successfully"
}

# Function to build and start services
start_services() {
    print_status "Building and starting KarmaChain services..."
    
    # Build and start services in detached mode
    $DOCKER_COMPOSE up -d --build
    
    print_success "Services started successfully"
}

# Function to check service health
check_health() {
    print_status "Checking service health..."
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check MongoDB
    if $DOCKER_COMPOSE exec -T mongo mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
        print_success "MongoDB is healthy"
    else
        print_error "MongoDB health check failed"
        return 1
    fi
    
    # Check Karma API
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Karma API is healthy"
    else
        print_error "Karma API health check failed"
        return 1
    fi
    
    # Check unified event endpoint
    if curl -f -X POST http://localhost:8000/v1/karma/event \
        -H "Content-Type: application/json" \
        -d '{"event_type": "stats_request", "user_id": "test_user", "data": {}}' >/dev/null 2>&1; then
        print_success "Unified event gateway is operational"
    else
        print_warning "Unified event gateway might not be fully ready yet"
    fi
    
    # Check Mongo Express
    if curl -f http://localhost:8081 >/dev/null 2>&1; then
        print_success "Mongo Express is accessible"
    else
        print_warning "Mongo Express might not be ready yet"
    fi
}

# Function to display service information
show_info() {
    print_success "KarmaChain is now running!"
    echo
    echo -e "${BLUE}Services:${NC}"
    echo "  • Karma API:        http://localhost:8000"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • MongoDB:          localhost:27017"
    echo "  • Mongo Express:    http://localhost:8081"
    echo
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "  • View logs:        $DOCKER_COMPOSE logs -f"
    echo "  • Stop services:    $DOCKER_COMPOSE down"
    echo "  • Restart services: $DOCKER_COMPOSE restart"
    echo "  • Rebuild:          $DOCKER_COMPOSE up -d --build"
    echo
    echo -e "${BLUE}Testing:${NC}"
    echo "  • Run integration demo: docker-compose exec karma-api python tests/integration_demo.py"
    echo "  • Run all tests:        docker-compose exec karma-api python test_runner.py"
    echo "  • Test unified events:  docker-compose exec karma-api python test_unified_event_with_db.py"
    echo "  • Test file uploads:    docker-compose exec karma-api python test_atonement_storage.py"
    echo "  • Test event endpoints: docker-compose exec karma-api python test_event_endpoint.py"
    echo
    echo -e "${BLUE}Unified Event Gateway:${NC}"
    echo "  • Single endpoint:      POST http://localhost:8000/v1/karma/event"
    echo "  • File uploads:         POST http://localhost:8000/v1/karma/event/with-file"
    echo "  • Event types:          life_event, atonement, atonement_with_file, appeal, death_event, stats_request"
    echo
    echo -e "${BLUE}File Upload Support:${NC}"
    echo "  • Upload directory:     ./uploads"
    echo "  • Max file size:      Configurable via MAX_FILE_SIZE"
    echo "  • Allowed types:      jpg, jpeg, png, pdf, doc, docx"
    echo "  • Cleanup:            Automatic with retention policy"
}

# Function to handle cleanup on exit
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Script failed. Check logs with: $DOCKER_COMPOSE logs"
    fi
}

# Function to clean up
cleanup() {
    print_status "Cleaning up..."
    $DOCKER_COMPOSE down -v
    rm -rf logs/* mongo-init/* uploads/* backups/*
    print_success "Cleanup completed with unified event system support"
}

# Set trap for cleanup
trap cleanup EXIT

# Main execution
main() {
    print_status "Starting KarmaChain local development setup..."
    echo
    
    # Check prerequisites
    check_docker
    check_docker_compose
    
    # Setup environment
    create_env_file
    create_directories
    create_mongo_init
    
    # Pull images
    pull_images
    
    # Start services
    start_services
    
    # Health check
    if check_health; then
        show_info
    else
        print_error "Some services failed health checks. Check logs with: $DOCKER_COMPOSE logs"
        exit 1
    fi
}

# Run main function
main "$@"