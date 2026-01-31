# Docker Deployment Guide

## Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your actual credentials
# IMPORTANT: Change passwords and API keys!
```

### 2. Start Services

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Run Database Migrations

```bash
docker-compose exec app piccolo migrations forwards all
```

### 4. Access Application

- **Main App**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

## Architecture

The application consists of 5 services:

1. **postgres** - PostgreSQL 16 database with persistent storage
2. **redis** - Redis message broker and cache
3. **app** - Main FastAPI application (port 8000)
4. **poller** - Event polling service from HikCentral
5. **worker** - Background job processor

## Persistent Data

### Database Volumes

All data is stored in named Docker volumes that persist across container restarts:

- `zim-attendance-postgres-data` - PostgreSQL data
- `zim-attendance-redis-data` - Redis persistence

**Your data is safe** - volumes are NOT deleted when you:

- Stop containers (`docker-compose down`)
- Restart containers (`docker-compose restart`)
- Rebuild images (`docker-compose build`)

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect zim-attendance-postgres-data

# Backup volume
docker run --rm -v zim-attendance-postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz /data

# Restore volume
docker run --rm -v zim-attendance-postgres-data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres-backup.tar.gz -C /
```

## Common Commands

### Using Make (Recommended)

```bash
make build       # Build images
make up          # Start services
make down        # Stop services
make logs        # View logs
make migrate     # Run migrations
make backup      # Backup database
make dev         # Start in dev mode
```

### Using Docker Compose Directly

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f app
docker-compose logs -f worker
docker-compose logs -f poller

# Restart specific service
docker-compose restart app

# Scale workers
docker-compose up -d --scale worker=3

# Execute command in container
docker-compose exec app python -c "print('Hello')"

# Shell into container
docker-compose exec app /bin/bash
```

## Database Management

### Migrations

```bash
# Run migrations
docker-compose exec app piccolo migrations forwards all

# Create new migration
docker-compose exec app piccolo migrations new hr --auto

# Rollback migration
docker-compose exec app piccolo migrations backwards hr
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres zim_attendance_db

# Create backup
docker-compose exec postgres pg_dump -U postgres zim_attendance_db > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U postgres zim_attendance_db < backup.sql
```

## Development Mode

Development mode includes:

- Hot reload for code changes
- Debug logging enabled
- Source code mounted as volume

```bash
# Start in dev mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or using make
make dev
```

## Production Deployment

### 1. Update Configuration

```bash
# Edit .env
PRODUCTION=true
DEBUG=false
LOGGING__LOG_STD_LEVEL="INFO"

# Set strong passwords
DATABASE__POSTGRES_PASSWORD="strong_random_password"
PASSWORD="admin_strong_password"
```

### 2. Enable HTTPS (Recommended)

Add nginx reverse proxy:

```yaml
# docker-compose.prod.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
```

### 3. Start Production

```bash
docker-compose up -d
```

## Monitoring

### Health Checks

```bash
# Check service health
docker-compose ps

# All services should show "healthy" or "running"
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 worker

# Application logs are also in ./logs/
tail -f logs/access.log
tail -f logs/error.log
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs app

# Check events
docker-compose events

# Rebuild image
docker-compose build --no-cache app
docker-compose up -d app
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec app python -c "from core.db import database_connection; import asyncio; asyncio.run(database_connection())"
```

### Reset Everything (CAUTION)

```bash
# Stop and remove containers, networks
docker-compose down

# Remove volumes (THIS DELETES DATA!)
docker volume rm zim-attendance-postgres-data
docker volume rm zim-attendance-redis-data

# Start fresh
docker-compose up -d
```

## Security Best Practices

1. **Change Default Passwords**: Update all passwords in `.env`
2. **Use Secrets**: In production, use Docker secrets instead of environment variables
3. **Network Isolation**: Services communicate via internal network
4. **Non-Root User**: Application runs as non-root user
5. **Resource Limits**: Set memory/CPU limits in production
6. **Regular Backups**: Automate database backups
7. **Update Images**: Regularly update base images

## Performance Tuning

### Scale Workers

```bash
# Run multiple workers
docker-compose up -d --scale worker=3
```

### Resource Limits

```yaml
# Add to docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 1G
        reservations:
          cpus: "0.5"
          memory: 512M
```

### PostgreSQL Tuning

Create `docker/postgres/postgresql.conf`:

```conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
max_connections = 200
```
