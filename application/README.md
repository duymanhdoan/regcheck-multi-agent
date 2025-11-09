# Application Service

File processing service with MCP data enrichment for the Internal File Processing System.

## Overview

The Application service is responsible for:
- Downloading files from S3
- Fetching data from MCP servers via AgentGateway
- Processing files with MCP data enrichment
- Uploading results to S3
- Generating presigned download URLs
- Tracking processing status

## Architecture

```
Application Service
├── S3 Client (download/upload files)
├── MCP Client (call MCP servers via AgentGateway)
├── File Processor (orchestrate processing workflow)
└── FastAPI App (REST API endpoints)
```

## API Endpoints

### POST /process
Start file processing with MCP data enrichment.

**Request:**
```json
{
  "file_id": "file-123",
  "user_id": "user-456",
  "input_s3_key": "uploads/user-456/document.pdf",
  "mcp_server_type": "finance",
  "mcp_tool_name": "get_financial_data",
  "mcp_arguments": {
    "user_id": "user-456",
    "data_type": "balance"
  }
}
```

**Response (202 Accepted):**
```json
{
  "processing_id": "uuid",
  "status": "pending",
  "message": "Processing started successfully"
}
```

### GET /status/{processing_id}
Get processing job status.

**Response:**
```json
{
  "processing_id": "uuid",
  "status": "completed",
  "started_at": "2025-11-09T10:00:00Z",
  "completed_at": "2025-11-09T10:00:05Z",
  "processing_time_ms": 5432,
  "error_message": null
}
```

### GET /download/{processing_id}
Get presigned download URL for processed file.

**Response:**
```json
{
  "processing_id": "uuid",
  "download_url": "https://s3.amazonaws.com/...",
  "expires_at": "2025-11-09T11:00:00Z",
  "output_s3_key": "processed/user-456/result.json"
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "application",
  "version": "1.0.0"
}
```

## Configuration

Environment variables:

- `SERVICE_NAME`: Service name (default: "application")
- `SERVICE_PORT`: Service port (default: 8000)
- `AWS_REGION`: AWS region (default: "ap-southeast-1")
- `S3_BUCKET_NAME`: S3 bucket name
- `AGENTGATEWAY_MCP_URL`: AgentGateway MCP endpoint URL
- `SERVICE_TOKEN`: Service authentication token
- `PROCESSING_TIMEOUT`: Processing timeout in seconds (default: 300)
- `LOG_LEVEL`: Logging level (default: "INFO")

## Development

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Locally

```bash
# Set environment variables
export S3_BUCKET_NAME=app-files-dev-ap-southeast-1
export AGENTGATEWAY_MCP_URL=http://localhost:8081
export SERVICE_TOKEN=your-token

# Run the service
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Build Docker Image

```bash
docker build -t application:latest .
```

### Run Docker Container

```bash
docker run -p 8000:8000 \
  -e S3_BUCKET_NAME=app-files-dev-ap-southeast-1 \
  -e AGENTGATEWAY_MCP_URL=http://agentgateway:8081 \
  -e SERVICE_TOKEN=your-token \
  application:latest
```

## Deployment

### Build and Push to ECR

```bash
# Authenticate with ECR
aws ecr get-login-password --region ap-southeast-1 | \
  docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.ap-southeast-1.amazonaws.com

# Build image
docker build -t application:latest .

# Tag image
docker tag application:latest \
  ${AWS_ACCOUNT_ID}.dkr.ecr.ap-southeast-1.amazonaws.com/application:latest

# Push image
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.ap-southeast-1.amazonaws.com/application:latest
```

### Deploy to ECS

```bash
# Update ECS service
aws ecs update-service \
  --cluster dev-ecs-cluster \
  --service application-service \
  --force-new-deployment
```

## Processing Workflow

1. **Receive Request**: API receives processing request with file details
2. **Download File**: Download file from S3 uploads/ folder
3. **Fetch MCP Data**: Call MCP server via AgentGateway to fetch enrichment data
4. **Process File**: Enrich file with MCP data
5. **Upload Result**: Upload processed result to S3 processed/ folder
6. **Generate URL**: Generate presigned download URL (1 hour expiration)
7. **Return Status**: Return processing status and download URL

## Error Handling

- **S3 Errors**: Retry with exponential backoff (3 attempts)
- **MCP Errors**: Retry with exponential backoff (3 attempts)
- **Processing Errors**: Mark job as failed with error message
- **Timeout**: Processing timeout after 300 seconds (configurable)

## Monitoring

- **Logs**: JSON-formatted logs to CloudWatch
- **Metrics**: CPU, memory, request count, processing time
- **Health Check**: `/health` endpoint for ALB health checks

## Security

- **IAM Role**: Task role with S3 GetObject/PutObject permissions
- **Service Token**: Authentication for MCP Gateway calls
- **Encryption**: S3 server-side encryption (SSE-S3)
- **Network**: Runs in private subnet, no direct internet access
