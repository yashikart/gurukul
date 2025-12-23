# Deployment Notes for KarmaChain

## System Requirements
- Docker and Docker Compose
- Python 3.11+
- MongoDB 6.0+
- 2GB+ RAM recommended (4GB+ for production with file uploads)
- 10GB+ storage for data (20GB+ recommended for production with event retention)
- Network bandwidth: 1Mbps+ (10Mbps+ for production with file uploads)

## Deployment Options

### Local Development
1. Clone the repository and navigate to the project directory
2. Copy `env.example` to `.env` and configure your settings
3. Run the development setup:
   ```bash
   docker-compose up -d
   ```
4. Access the API at http://localhost:8000
5. MongoDB Express available at http://localhost:8081 (admin/admin)

### Production Deployment
1. Use Docker Compose with production overrides:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```
2. Set up proper authentication and TLS termination
3. Configure MongoDB for persistence and replication
4. Set up monitoring and alerting

### Kubernetes Deployment
1. Use the provided Kubernetes manifests in `k8s/` directory
2. Configure ConfigMaps and Secrets for environment variables
3. Set up persistent volumes for MongoDB
4. Configure ingress for external access

## Environment Configuration

### Required Environment Variables
- `MONGODB_URI`: MongoDB connection string
- `SECRET_KEY`: Application secret key
- `DEBUG`: Set to `false` for production
- `LOG_LEVEL`: Logging level (info, warning, error)

### Unified Event System Configuration
- `MAX_FILE_SIZE`: Maximum file upload size in bytes (default: 1MB)
- `EVENT_RETENTION_DAYS`: Days to keep events in database (default: 90)
- `EVENT_CLEANUP_INTERVAL`: Cleanup interval in seconds (default: 86400)
- `UPLOAD_DIR`: Directory for temporary file uploads
- `ALLOWED_FILE_TYPES`: Comma-separated list of allowed file extensions
- `FILE_UPLOAD_TIMEOUT`: File upload timeout in seconds (default: 30)

### Optional Configuration
- `API_PORT`: API server port (default: 8000)
- `API_RATE_LIMIT`: Rate limit per minute (default: 1000)
- `EVENT_BATCH_SIZE`: Batch processing size for event cleanup (default: 1000)

## Scaling Considerations

### Horizontal Scaling
- The API is stateless and can be horizontally scaled
- Use a load balancer for multiple API instances
- Configure sticky sessions if needed for WebSocket connections
- File upload handling may require shared storage (NFS, S3)

### Database Scaling
- MongoDB should be configured with replica sets for HA
- Consider sharding for large datasets, especially karma_events collection
- Use connection pooling for better performance
- Monitor MongoDB query performance, especially for karma_events collection
- Use appropriate indexes for user queries and event lookups

### Caching
- Consider Redis for session management and caching frequently accessed data
- Implement CDN for static assets and file uploads in production environments

### Unified Event System Scaling
- karma_events collection can grow large - implement proper indexing
- Consider sharding karma_events collection by timestamp or user_id
- Implement event cleanup jobs to manage data retention
- Monitor file upload disk usage and implement cleanup policies

## Security Considerations

### Network Security
- Use Docker networks to isolate services
- Configure firewall rules for database access
- Use TLS for all external communications

### Data Security
- Encrypt sensitive data at rest
- Use strong passwords for database access
- Implement proper backup encryption

### API Security
- Implement rate limiting and DDoS protection
- Use JWT tokens for authentication
- Validate all input data

### Application Security
- Use strong SECRET_KEY in production
- Enable HTTPS/TLS in production
- Implement proper input validation
- Use parameterized queries for MongoDB
- Validate file uploads (type, size, content)
- Sanitize file names to prevent path traversal

### Database Security
- Use strong MongoDB passwords
- Enable MongoDB authentication
- Restrict network access to MongoDB
- Regular security updates for MongoDB
- Implement database access controls for karma_events collection

### File Upload Security
- Validate file types and extensions
- Scan uploaded files for malware
- Implement file size limits
- Store files outside web root
- Use secure file naming conventions

## Monitoring and Observability

### Health Checks
- API health endpoint: `/health`
- Database health: Built into MongoDB container
- Service dependencies: Configured in docker-compose
- Unified event system health: Check karma_events collection status

### Metrics
- Prometheus metrics: `/metrics` endpoint
- Application logs: Available via `docker-compose logs`
- Database metrics: Available through MongoDB monitoring
- Event processing success/failure rates
- File upload success/failure rates
- Storage usage for file uploads
- Event cleanup job performance

### Logging
- Structured JSON logging for better parsing
- Log rotation configured in containers
- Centralized logging recommended for production
- Event processing logs for unified event system
- File upload processing logs

### Key Performance Indicators (KPIs)
- Event processing latency (target: <100ms)
- File upload processing time (target: <5s)
- Event storage growth rate
- System availability (target: 99.9%)
- Error rate for event processing (target: <1%)

## Backup and Recovery

### Data Backup
- MongoDB data volume backup (including karma_events collection)
- Application logs backup
- Configuration backup
- File upload backup (if using local storage)

### Recovery Procedures
- MongoDB data recovery from backup
- Application redeployment
- Configuration restoration
- File upload restoration (if applicable)

### Backup Strategy
- Daily automated backups for MongoDB
- Weekly configuration backups
- Log rotation with retention policy
- Test recovery procedures regularly
- Document recovery time objectives (RTO) and recovery point objectives (RPO)

### Application State
- Backup configuration files and environment variables
- Document custom configurations and modifications
- Maintain deployment scripts and procedures

## Troubleshooting

### Common Issues
- Check logs with `docker-compose logs karma-api`
- Verify MongoDB connection with `docker-compose exec mongo mongosh`
- API diagnostics available at `/debug` (disable in production)
- File upload failures
- Event processing errors

### Debug Commands
```bash
# View logs
docker-compose logs -f karma-api

# Check container status
docker-compose ps

# Access MongoDB
docker-compose exec mongo mongosh -u admin -p admin123

# Restart services
docker-compose restart karma-api

# Check file upload directory
docker-compose exec karma-api ls -la /app/uploads

# Monitor event processing
docker-compose exec mongo mongosh -u admin -p admin123 --eval "use karmachain; db.karma_events.find().limit(5)"

# Check disk usage
docker-compose exec karma-api df -h
```

### Event System Issues
- Check karma_events collection for stuck events
- Verify file upload permissions and disk space
- Monitor event processing logs for errors
- Check event cleanup job status

### Performance Issues
- Monitor database query performance
- Check API response times and error rates
- Review resource utilization (CPU, memory, disk)

### Database Issues
- Check MongoDB logs for connection errors
- Verify database indexes are properly created
- Monitor database size and growth patterns

## Maintenance

### Regular Tasks
- Update Docker images regularly
- Monitor disk usage and clean up logs
- Review and rotate logs
- Check system health
- Monitor karma_events collection growth
- Clean up old file uploads
- Review event retention policies

### Updates
- Follow semantic versioning for releases
- Test updates in staging environment first
- Implement rolling updates for zero downtime
- Backup before major updates

### Event System Maintenance
- Monitor karma_events collection size and growth
- Run event cleanup jobs regularly
- Archive old events if needed
- Optimize database indexes for event queries
- Monitor file upload storage usage
- Clean up temporary file uploads

### Cleanup
- Regular cleanup of old logs and temporary files
- Monitor disk usage and implement cleanup policies
- Archive old data according to retention policies