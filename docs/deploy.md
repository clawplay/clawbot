# Deployment Guide

This guide covers deployment options for baibo, from development setups to production deployments.

## Deployment Options

### 1. Development Mode (File Backend)

**Use Case**: Local development, testing, simple deployments
**Backend**: File-based memory storage
**Setup**: Zero configuration required

```bash
# Clone and install
git clone https://github.com/clawplay/baibo.git
cd baibo
uv sync

# Configure
uv run baibo onboard

# Start development server
uv run baibo gateway
```

**Features**:
- Daily and long-term memory in Markdown files
- No database setup required
- Ideal for development and small-scale use
- Easy to backup and migrate

### 2. Production Mode (PostgreSQL Backend)

**Use Case**: Production deployments, multi-user systems, large-scale usage
**Backend**: PostgreSQL with pgvector and pgmq extensions
**Setup**: Docker container provided

#### 2.1 Self-Hosted PostgreSQL

**Prerequisites**:
- Docker and Docker Compose
- PostgreSQL 14+ with pgvector and pgmq extensions

**Setup Steps**:

1. **Start PostgreSQL with extensions**:
```bash
# Using provided Docker setup
docker-compose -f docker/pg.yml up -d
```

2. **Configure baibo**:
```bash
# Run onboard with PostgreSQL backend
uv run baibo onboard --backend postgres
```

3. **Verify setup**:
```bash
# Test database connection
uv run baibo db check

# Start services
uv run baibo gateway
```

**Configuration**:
```yaml
# config.yaml
database:
  url: "postgresql://user:password@localhost:5432/baibo"
  pool_size: 10
  max_overflow: 20
```

#### 2.2 Cloud PostgreSQL Options

##### Supabase (Recommended)

**⚠️ Important**: When using Supabase, you **must** use Session Pooler mode for optimal performance.

**Setup Steps**:

1. **Create Supabase Project**:
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Note your project URL and API key

2. **Enable Required Extensions**:
   ```sql
   -- In Supabase SQL Editor
   CREATE EXTENSION IF NOT EXISTS vector;
   CREATE EXTENSION IF NOT EXISTS pgmq;
   ```

3. **Configure Connection**:
   ```yaml
   # config.yaml
   database:
     # Use Session Pooler URL (NOT Direct Connection)
     url: "postgresql://postgres:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
     pool_size: 5
     max_overflow: 10
   ```

**Why Session Pooler?**
- **Connection Pooling**: Manages database connections efficiently
- **Better Performance**: Reduces connection overhead
- **Cost Optimization**: Fewer active connections to your database
- **Reliability**: Automatic connection recovery and load balancing

**Connection String Format**:
```
postgresql://postgres:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

##### Other Cloud Providers

**AWS RDS**:
```yaml
database:
  url: "postgresql://user:password@your-rds-instance.region.rds.amazonaws.com:5432/baibo"
```

**Google Cloud SQL**:
```yaml
database:
  url: "postgresql://user:password@your-instance:5432/baibo"
```

**Neon**:
```yaml
database:
  url: "postgresql://user:password@your-neon-project.neon.tech:5432/baibo"
```

## Production Deployment

### Docker Deployment

1. **Build Docker image**:
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN uv sync

EXPOSE 8000
CMD ["uv", "run", "baibo", "gateway"]
```

2. **Docker Compose setup**:
```yaml
# docker-compose.yml
version: '3.8'

services:
  baibo:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/baibo
    depends_on:
      - postgres
    volumes:
      - ./config.yaml:/app/config.yaml

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: baibo
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Environment Variables

```bash
# Required
DATABASE_URL="postgresql://user:password@host:5432/baibo"

# Optional
OPENAI_API_KEY="your-openai-key"
ANTHROPIC_API_KEY="your-anthropic-key"
EMBEDDING_API_KEY="your-embedding-key"

# Performance tuning
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

### Monitoring and Maintenance

#### Health Checks

```bash
# Check database connection
uv run baibo db check

# Check embedding queue
uv run baibo queue status

# System health
uv run baibo health
```

#### Backup Strategy

**PostgreSQL Backup**:
```bash
# Daily backup
pg_dump baibo > backup_$(date +%Y%m%d).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump baibo > $BACKUP_DIR/baibo_$DATE.sql
```

**File Backend Backup**:
```bash
# Simple tar backup
tar -czf memory_backup_$(date +%Y%m%d).tar.gz memory/
```

#### Performance Monitoring

Key metrics to monitor:
- Database connection pool usage
- Embedding queue length
- Memory query response times
- API response latency

## Scaling Considerations

### Horizontal Scaling

- **Stateless Design**: Multiple gateway instances can share the same database
- **Load Balancing**: Use nginx or cloud load balancer
- **Session Management**: Ensure sticky sessions if needed

### Database Scaling

- **Read Replicas**: For read-heavy workloads
- **Connection Pooling**: Essential for multi-instance deployments
- **Index Optimization**: Monitor and optimize memory table indexes

## Security Best Practices

1. **Database Security**:
   - Use strong passwords
   - Enable SSL connections
   - Restrict network access

2. **API Keys**:
   - Store in environment variables
   - Rotate regularly
   - Use key management services in production

3. **Network Security**:
   - Use VPNs for database access
   - Implement rate limiting
   - Monitor for unusual activity

## Troubleshooting

### Common Issues

**Database Connection Errors**:
```bash
# Test connection manually
psql $DATABASE_URL

# Check if extensions are installed
\dx
```

**Embedding Queue Backlog**:
```bash
# Check queue status
uv run baibo queue status

# Process queue manually
uv run baibo queue process
```

**Memory Search Issues**:
```bash
# Verify pgvector extension
SELECT * FROM pg_extension WHERE extname = 'vector';

# Check embedding indexes
\d+ memory_conversation
```

### Performance Optimization

1. **Database Indexes**:
   ```sql
   -- Add composite indexes for common queries
   CREATE INDEX idx_memory_daily_date_content ON memory_daily(created_at, content);
   ```

2. **Connection Pooling**:
   ```yaml
   database:
     pool_size: 20
     max_overflow: 30
     pool_timeout: 30
     pool_recycle: 3600
   ```

3. **Caching**:
   - Enable query caching for frequent memory lookups
   - Consider Redis for session caching

## Migration Guide

### From File to PostgreSQL Backend

1. **Backup existing data**:
```bash
cp -r memory/ memory_backup/
```

2. **Set up PostgreSQL**:
```bash
docker-compose -f docker/pg.yml up -d
uv run baibo db migrate
```

3. **Migrate data**:
```bash
uv run baibo migrate --from-file --to-postgres
```

4. **Update configuration**:
```yaml
memory:
  backend: postgres
```

This migration preserves all existing daily and long-term memories while enabling the full hybrid memory system.