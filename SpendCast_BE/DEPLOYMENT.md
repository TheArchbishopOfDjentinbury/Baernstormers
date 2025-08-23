# SpendCast Backend Deployment Guide

Guide for deploying FastAPI application SpendCast to Google Cloud Run.

## Prerequisites

1. **Google Cloud CLI**: Install and configure gcloud CLI

   ```bash
   # Install gcloud (macOS)
   brew install google-cloud-sdk

   # Authentication
   gcloud auth login

   # Project configuration
   gcloud config set project spendcast-backend
   ```

2. **Docker** (for local build, optional)
   ```bash
   # macOS
   brew install docker
   ```

## Quick Deployment

1. **Run the deployment script**:

   ```bash
   chmod +x dockerize.sh
   ./dockerize.sh
   ```

2. **Choose build method**:

   - `1` - Local Docker build (requires installed Docker)
   - `2` - Google Cloud Build (recommended, doesn't require local Docker)

3. **Configure environment variables** when prompted by the script

## File Structure for Deployment

```
SpendCast_BE/
├── Dockerfile              # Docker container configuration
├── .dockerignore           # Files to exclude from build
├── dockerize.sh            # Automatic deployment script
├── env.production.example  # Environment variables example
├── requirements.txt        # Python dependencies
└── main.py                # FastAPI application entry point
```

## Dockerfile

Optimized Dockerfile for FastAPI:

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8080

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc curl

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create user for security
RUN adduser --disabled-password --gecos '' --shell /bin/bash user
USER user

EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Start application
CMD uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
```

## Environment Variables

Copy `env.production.example` and configure:

```bash
# Main settings
GRAPHDB_URL=http://your-graphdb-instance:7200/repositories/spendcast
GRAPHDB_USER=your-username
GRAPHDB_PASSWORD=your-password
OPENAI_API_KEY=your-openai-key
SECRET_KEY=your-production-secret-key
```

## Management Commands

After deployment:

```bash
# View logs
gcloud run services logs read spendcast-backend --region=europe-west3

# Update service
./dockerize.sh

# Delete service
gcloud run services delete spendcast-backend --region=europe-west3

# Redirect traffic to new revision
gcloud run services update-traffic spendcast-backend --to-latest --region=europe-west3
```

## Deployment Verification

1. **Health Check**: `https://your-service-url/health`
2. **API Documentation**: `https://your-service-url/docs`
3. **Database Check**: `https://your-service-url/api/v1/database/check`

## Cloud Run Settings

The script automatically configures:

- **Region**: europe-west3
- **Memory**: 1Gi
- **CPU**: 1 vCPU
- **Maximum instances**: 10
- **Timeout**: 300 seconds
- **Concurrency**: 100 requests per instance
- **Port**: 8080

## Security

- Application runs as non-root user
- Health checks enabled
- HTTPS support out of the box in Cloud Run
- Environment variables can be safely stored in Secret Manager

## Monitoring

Cloud Run automatically provides:

- CPU/Memory usage metrics
- Application logs
- Request tracing
- Automatic scaling

## Troubleshooting

### Issue: "gcloud not found"

```bash
# Install Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

### Issue: "Permission denied"

```bash
# Give execute permissions to the script
chmod +x dockerize.sh
```

### Issue: "Docker not running"

```bash
# Start Docker Desktop or use Cloud Build (option 2)
open -a Docker
```

### Issue: GraphDB not accessible

Make sure:

- GraphDB URL is accessible from Cloud Run
- Credentials are properly configured in environment variables
- Firewall rules allow connections

## Additional Resources

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
