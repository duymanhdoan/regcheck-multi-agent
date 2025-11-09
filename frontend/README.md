# Langflow Frontend Service

This directory contains the Langflow-based frontend service for the Internal File Processing System. Langflow provides a visual interface for building and managing LLM workflows.

## Overview

The frontend service uses [Langflow](https://github.com/logspace-ai/langflow), an open-source UI for building and testing LLM flows. It's deployed as a containerized service on AWS Fargate with custom components for backend integration.

### Key Features

- **Visual Workflow Builder**: Drag-and-drop interface for creating LLM workflows
- **Custom Components**: Pre-built components for AgentGateway, S3, and MCP server integration
- **Persistent Storage**: EFS-backed storage for workflow configurations and data
- **Auto Scaling**: Scales from 1-4 tasks based on CPU utilization
- **Session Management**: Sticky sessions for consistent user experience

## Architecture

```
Internet → ALB (Port 80) → Langflow (Port 7860)
                              ↓
                         AgentGateway API
                              ↓
                         Backend Services
```

### Resource Allocation

- **CPU**: 1 vCPU
- **Memory**: 2 GB RAM
- **Storage**: EFS volume mounted at `/app/langflow`
- **Port**: 7860 (Langflow default)

## Docker Image

The frontend uses the official Langflow Docker image from Docker Hub with custom components:

- **Base Image**: `langflowai/langflow:latest`
- **Custom Components**: Located in `langflow_components/`
- **Additional Dependencies**: httpx, boto3

### Building the Image

```bash
# Build for dev environment
./build.sh dev

# Build for prod environment
./build.sh prod

# Build with specific tag
./build.sh dev v1.0.0
```

The build script:
1. Authenticates with ECR
2. Builds the Docker image with custom components
3. Tags the image appropriately
4. Pushes to ECR repository

## Custom Components

The frontend includes three custom Langflow components:

### 1. AgentGateway API Component

Integrates with the AgentGateway API for file processing operations.

**Use Cases**:
- Trigger file processing jobs
- Check processing status
- Retrieve processing results

### 2. S3 Operations Component

Provides S3 file operations using IAM role credentials.

**Use Cases**:
- Upload files to S3
- Download processed files
- List files in buckets
- Delete temporary files

### 3. MCP Server Client Component

Interacts with MCP servers (Finance, HR, Legal) through AgentGateway.

**Use Cases**:
- Fetch financial data
- Retrieve employee information
- Access legal documents
- Query compliance information

See `langflow_components/README.md` for detailed documentation.

## Environment Variables

The following environment variables are configured in the ECS task definition:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `LANGFLOW_DATABASE_URL` | SQLite database location | `sqlite:////app/langflow/langflow.db` |
| `LANGFLOW_CONFIG_DIR` | Configuration directory | `/app/langflow` |
| `LANGFLOW_LOG_LEVEL` | Logging level | `INFO` |
| `LANGFLOW_HOST` | Bind host | `0.0.0.0` |
| `LANGFLOW_PORT` | Service port | `7860` |
| `LANGFLOW_BACKEND_URL` | AgentGateway API URL | `http://agentgateway-service.dev.local:8080` |
| `AWS_REGION` | AWS region | `ap-southeast-1` |
| `S3_BUCKET_NAME` | S3 bucket for files | `app-files-dev-ap-southeast-1` |

## Persistent Storage

Langflow data is stored on an EFS volume to persist across container restarts:

- **File System**: AWS EFS with encryption enabled
- **Mount Point**: `/app/langflow`
- **Access Point**: Dedicated EFS access point with UID/GID 1000
- **Contents**:
  - `langflow.db`: SQLite database with workflows and configurations
  - Flow definitions and components
  - User preferences and settings

### EFS Configuration

```hcl
# EFS File System
resource "aws_efs_file_system" "langflow" {
  encrypted = true
  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }
}

# EFS Access Point
resource "aws_efs_access_point" "langflow" {
  posix_user {
    gid = 1000
    uid = 1000
  }
  root_directory {
    path = "/langflow"
  }
}
```

## Deployment

### Prerequisites

1. ECR repository created
2. VPC and subnets configured
3. ALB and target group created
4. EFS file system provisioned
5. IAM roles configured

### Deploy to Dev

```bash
# Build and push image
cd frontend
./build.sh dev

# Update ECS service (via Terraform)
cd ../terraform/environments/dev
terraform apply

# Or force new deployment
aws ecs update-service \
  --cluster dev-ecs-cluster \
  --service frontend-service \
  --force-new-deployment \
  --region ap-southeast-1
```

### Deploy to Prod

```bash
# Build and push image
cd frontend
./build.sh prod

# Update ECS service (via Terraform)
cd ../terraform/environments/prod
terraform apply

# Or force new deployment
aws ecs update-service \
  --cluster prod-ecs-cluster \
  --service frontend-service \
  --force-new-deployment \
  --region ap-southeast-1
```

## Accessing Langflow

### Via ALB

```
http://<alb-dns-name>
```

Get the ALB DNS name:
```bash
aws elbv2 describe-load-balancers \
  --names dev-alb-ap-southeast-1 \
  --query 'LoadBalancers[0].DNSName' \
  --output text
```

### Health Check

```bash
curl http://<alb-dns-name>/health
```

## Using Langflow

### Creating a Flow

1. Access Langflow UI via ALB URL
2. Click "New Flow" to create a workflow
3. Drag components from the sidebar
4. Connect components to build your flow
5. Configure component parameters
6. Save and test the flow

### Example Flow: File Processing

```
1. S3 Operations (upload)
   ↓
2. AgentGateway API (POST /api/process)
   ↓
3. Wait/Delay Component
   ↓
4. AgentGateway API (GET /api/status/{id})
   ↓
5. S3 Operations (download)
```

### Example Flow: MCP Data Enrichment

```
1. MCP Server Client (Finance - get_financial_data)
   ↓
2. MCP Server Client (HR - get_employee_data)
   ↓
3. Data Combiner Component
   ↓
4. S3 Operations (upload result)
```

## Monitoring

### CloudWatch Logs

View logs in CloudWatch:
```bash
aws logs tail /ecs/dev/frontend --follow
```

### ECS Service Metrics

Monitor service health:
```bash
aws ecs describe-services \
  --cluster dev-ecs-cluster \
  --services frontend-service
```

### Auto Scaling

Check current task count:
```bash
aws ecs describe-services \
  --cluster dev-ecs-cluster \
  --services frontend-service \
  --query 'services[0].{desired:desiredCount,running:runningCount,pending:pendingCount}'
```

## Troubleshooting

### Container Won't Start

1. Check CloudWatch logs for errors
2. Verify ECR image exists and is accessible
3. Check EFS mount target is available
4. Verify IAM role permissions

```bash
# Check task status
aws ecs describe-tasks \
  --cluster dev-ecs-cluster \
  --tasks <task-id>
```

### Health Check Failing

1. Verify Langflow is listening on port 7860
2. Check security group allows ALB → Container traffic
3. Review health check configuration in target group

```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>
```

### Custom Components Not Loading

1. Verify components are copied into image
2. Check `LANGFLOW_COMPONENTS_PATH` is set
3. Review component import errors in logs
4. Ensure dependencies (httpx, boto3) are installed

```bash
# Exec into running container
aws ecs execute-command \
  --cluster dev-ecs-cluster \
  --task <task-id> \
  --container frontend \
  --interactive \
  --command "/bin/bash"
```

### EFS Mount Issues

1. Check EFS mount target is in correct subnet
2. Verify security group allows NFS traffic (port 2049)
3. Check IAM role has EFS permissions
4. Review EFS access point configuration

```bash
# Check EFS mount targets
aws efs describe-mount-targets \
  --file-system-id <fs-id>
```

### Session Stickiness Issues

1. Verify ALB target group has stickiness enabled
2. Check cookie duration is appropriate (3600s)
3. Review ALB access logs for session routing

## Security

### IAM Permissions

The frontend task role has:
- **S3**: PutObject to `uploads/*`
- **EFS**: ClientMount, ClientWrite, ClientRootAccess

### Network Security

- Deployed in private subnet
- No public IP assigned
- Accessible only via ALB
- Security group restricts inbound to ALB only

### Data Encryption

- EFS encryption at rest enabled
- EFS transit encryption enabled (TLS)
- S3 server-side encryption (SSE-S3)

## Maintenance

### Updating Langflow Version

1. Update base image in Dockerfile
2. Test locally
3. Build and push new image
4. Deploy to dev for testing
5. Deploy to prod after validation

### Backing Up Workflows

Workflows are stored in EFS. To backup:

```bash
# Create EFS backup
aws backup start-backup-job \
  --backup-vault-name default \
  --resource-arn <efs-arn> \
  --iam-role-arn <backup-role-arn>
```

### Scaling Configuration

Auto scaling is configured in Terraform:
- Min: 1 task
- Max: 4 tasks
- Target: 70% CPU utilization
- Scale out: 60 seconds
- Scale in: 300 seconds

To adjust:
```hcl
# In terraform/modules/ecs-fargate/main.tf
resource "aws_appautoscaling_target" "frontend" {
  max_capacity = 4  # Adjust as needed
  min_capacity = 1  # Adjust as needed
}
```

## Cost Optimization

### Current Costs (Approximate)

**Dev Environment**:
- Fargate: ~$30/month (1 task, 1 vCPU, 2GB)
- EFS: ~$5/month (1GB storage)
- ALB: ~$20/month
- **Total**: ~$55/month

**Prod Environment**:
- Fargate: ~$90/month (avg 3 tasks)
- EFS: ~$10/month (2GB storage)
- ALB: ~$20/month
- **Total**: ~$120/month

### Optimization Tips

1. Use EFS Infrequent Access for old workflows
2. Set appropriate auto scaling thresholds
3. Use Fargate Spot for dev environment
4. Clean up unused workflows periodically

## References

- [Langflow Documentation](https://docs.langflow.org/)
- [Langflow GitHub](https://github.com/logspace-ai/langflow)
- [Langflow Docker Hub](https://hub.docker.com/r/langflowai/langflow)
- [AWS Fargate Documentation](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [AWS EFS Documentation](https://docs.aws.amazon.com/efs/latest/ug/whatisefs.html)
