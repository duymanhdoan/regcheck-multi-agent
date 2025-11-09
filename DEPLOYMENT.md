# Deployment Guide

Complete deployment guide for the Internal File Processing System on AWS Fargate.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Docker installed and running
- Terraform >= 1.0
- AWS account with permissions for:
  - ECR (Elastic Container Registry)
  - ECS (Elastic Container Service)
  - VPC, ALB, S3, Cognito
  - IAM roles and policies

## Architecture Overview

The system consists of:
- **Frontend**: Langflow UI for user interaction
- **AgentGateway**: Dual-mode gateway (API + MCP routing)
- **Application**: File processing service
- **MCP Servers**: Finance, HR, and Legal data servers

## Deployment Steps

### Step 1: Set Environment Variables

```bash
# Set your AWS account ID
export AWS_ACCOUNT_ID=123456789012

# Set AWS region (default: ap-southeast-1)
export AWS_REGION=ap-southeast-1

# Set image tag (default: latest)
export IMAGE_TAG=latest

# Set environment (dev or prod)
export ENVIRONMENT=dev
```

### Step 2: Deploy Infrastructure with Terraform

#### 2.1 Initialize Terraform

```bash
cd terraform/environments/${ENVIRONMENT}
terraform init
```

#### 2.2 Review Infrastructure Plan

```bash
terraform plan -var-file=terraform.tfvars
```

Review the plan to ensure:
- VPC and networking resources
- ECR repositories
- ECS cluster and task definitions
- ALB and target groups
- S3 buckets
- Cognito user pool
- IAM roles and policies

#### 2.3 Apply Infrastructure

```bash
terraform apply -var-file=terraform.tfvars
```

Type `yes` when prompted to confirm.

**Expected Resources Created:**
- 1 VPC with public and private subnets
- 1 Application Load Balancer
- 1 ECS Fargate cluster
- 6 ECR repositories
- 1 S3 bucket
- 1 Cognito user pool
- Multiple IAM roles and security groups

#### 2.4 Get ECR Repository URLs

```bash
terraform output ecr_repository_urls
```

Save these URLs for the next step.

### Step 3: Build and Push Container Images

#### Option A: Build All Services at Once

```bash
# From project root
./build-all.sh
```

This will build and push all services:
- Frontend (Langflow)
- AgentGateway
- Application
- MCP Finance Server
- MCP HR Server
- MCP Legal Server

#### Option B: Build Services Individually

**Frontend:**
```bash
cd frontend
./build.sh
cd ..
```

**AgentGateway:**
```bash
cd agentgateway
./build.sh
cd ..
```

**Application:**
```bash
cd application
./build.sh
cd ..
```

**MCP Servers:**
```bash
cd mcp-servers
./build.sh finance
./build.sh hr
./build.sh legal
cd ..
```

### Step 4: Verify Images in ECR

```bash
# List repositories
aws ecr describe-repositories --region ${AWS_REGION}

# List images in a repository
aws ecr list-images \
  --repository-name frontend \
  --region ${AWS_REGION}
```

### Step 5: Deploy Services to ECS

#### 5.1 Update ECS Services

After infrastructure is created and images are pushed, update ECS services:

```bash
# Frontend service
aws ecs update-service \
  --cluster ${ENVIRONMENT}-ecs-cluster \
  --service frontend-service \
  --force-new-deployment \
  --region ${AWS_REGION}

# AgentGateway service
aws ecs update-service \
  --cluster ${ENVIRONMENT}-ecs-cluster \
  --service agentgateway-service \
  --force-new-deployment \
  --region ${AWS_REGION}

# Application service
aws ecs update-service \
  --cluster ${ENVIRONMENT}-ecs-cluster \
  --service application-service \
  --force-new-deployment \
  --region ${AWS_REGION}

# MCP Finance service
aws ecs update-service \
  --cluster ${ENVIRONMENT}-ecs-cluster \
  --service mcp-finance-service \
  --force-new-deployment \
  --region ${AWS_REGION}

# MCP HR service
aws ecs update-service \
  --cluster ${ENVIRONMENT}-ecs-cluster \
  --service mcp-hr-service \
  --force-new-deployment \
  --region ${AWS_REGION}

# MCP Legal service
aws ecs update-service \
  --cluster ${ENVIRONMENT}-ecs-cluster \
  --service mcp-legal-service \
  --force-new-deployment \
  --region ${AWS_REGION}
```

#### 5.2 Monitor Deployment

```bash
# Check service status
aws ecs describe-services \
  --cluster ${ENVIRONMENT}-ecs-cluster \
  --services frontend-service agentgateway-service application-service \
  --region ${AWS_REGION}

# Check running tasks
aws ecs list-tasks \
  --cluster ${ENVIRONMENT}-ecs-cluster \
  --region ${AWS_REGION}

# View task details
aws ecs describe-tasks \
  --cluster ${ENVIRONMENT}-ecs-cluster \
  --tasks <task-arn> \
  --region ${AWS_REGION}
```

### Step 6: Verify Deployment

#### 6.1 Get ALB DNS Name

```bash
cd terraform/environments/${ENVIRONMENT}
terraform output alb_dns_name
```

#### 6.2 Test Health Endpoints

```bash
ALB_DNS=$(terraform output -raw alb_dns_name)

# Frontend health check
curl http://${ALB_DNS}/health

# AgentGateway API health check
curl http://${ALB_DNS}/api/health

# AgentGateway MCP health check
curl http://${ALB_DNS}/mcp/health

# Application health check
curl http://${ALB_DNS}/app/health
```

#### 6.3 Test MCP Servers (Internal)

MCP servers are not exposed via ALB. Test from within the VPC or via AgentGateway.

### Step 7: Upload Sample Data to S3

```bash
# Get S3 bucket name
S3_BUCKET=$(cd terraform/environments/${ENVIRONMENT} && terraform output -raw s3_bucket_name)

# Create MCP data structure
aws s3 cp sample-data/finance/ s3://${S3_BUCKET}/mcp-data/finance/ --recursive
aws s3 cp sample-data/hr/ s3://${S3_BUCKET}/mcp-data/hr/ --recursive
aws s3 cp sample-data/legal/ s3://${S3_BUCKET}/mcp-data/legal/ --recursive
```

### Step 8: Create Cognito Users

```bash
# Get Cognito User Pool ID
USER_POOL_ID=$(cd terraform/environments/${ENVIRONMENT} && terraform output -raw cognito_user_pool_id)

# Create a test user
aws cognito-idp admin-create-user \
  --user-pool-id ${USER_POOL_ID} \
  --username testuser@example.com \
  --user-attributes Name=email,Value=testuser@example.com \
  --temporary-password TempPassword123! \
  --region ${AWS_REGION}

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id ${USER_POOL_ID} \
  --username testuser@example.com \
  --password Password123! \
  --permanent \
  --region ${AWS_REGION}
```

## Post-Deployment

### Access the Application

1. Open browser and navigate to: `http://<ALB_DNS_NAME>`
2. Login with Cognito credentials
3. Access Langflow UI

### Monitor Services

#### CloudWatch Logs

```bash
# View Frontend logs
aws logs tail /ecs/${ENVIRONMENT}/frontend --follow

# View AgentGateway logs
aws logs tail /ecs/${ENVIRONMENT}/agentgateway --follow

# View Application logs
aws logs tail /ecs/${ENVIRONMENT}/application --follow
```

#### CloudWatch Metrics

Navigate to CloudWatch Console:
- ECS Service metrics (CPU, Memory, Task count)
- ALB metrics (Request count, Response time, Error rates)
- Custom application metrics

### Scaling

#### Manual Scaling

```bash
# Scale up Frontend service
aws ecs update-service \
  --cluster ${ENVIRONMENT}-ecs-cluster \
  --service frontend-service \
  --desired-count 2 \
  --region ${AWS_REGION}
```

#### Auto Scaling (via Terraform)

Update `terraform.tfvars`:
```hcl
frontend_desired_count = 2
frontend_min_count     = 1
frontend_max_count     = 4
```

Apply changes:
```bash
cd terraform/environments/${ENVIRONMENT}
terraform apply -var-file=terraform.tfvars
```

## Troubleshooting

### Services Not Starting

1. Check ECS task logs:
```bash
aws ecs describe-tasks \
  --cluster ${ENVIRONMENT}-ecs-cluster \
  --tasks <task-arn> \
  --region ${AWS_REGION}
```

2. Check CloudWatch logs for errors

3. Verify IAM roles have correct permissions

4. Check security group rules

### Images Not Pulling

1. Verify ECR repository exists:
```bash
aws ecr describe-repositories --region ${AWS_REGION}
```

2. Check task execution role has ECR permissions

3. Verify image exists in ECR:
```bash
aws ecr list-images --repository-name frontend --region ${AWS_REGION}
```

### ALB Health Checks Failing

1. Verify health check endpoints are responding:
```bash
# From within VPC or via bastion
curl http://<service-private-ip>:8080/health
```

2. Check security group rules allow ALB to reach tasks

3. Review health check configuration in target groups

### MCP Servers Not Responding

1. Check MCP server logs in CloudWatch

2. Verify S3 data exists:
```bash
aws s3 ls s3://${S3_BUCKET}/mcp-data/ --recursive
```

3. Check IAM role has S3 read permissions

4. Test MCP endpoint via AgentGateway

## Rollback

### Rollback Service to Previous Version

```bash
# Get previous task definition revision
aws ecs describe-task-definition \
  --task-definition frontend-task \
  --region ${AWS_REGION}

# Update service to use previous revision
aws ecs update-service \
  --cluster ${ENVIRONMENT}-ecs-cluster \
  --service frontend-service \
  --task-definition frontend-task:<previous-revision> \
  --region ${AWS_REGION}
```

### Rollback Infrastructure

```bash
cd terraform/environments/${ENVIRONMENT}
terraform destroy -var-file=terraform.tfvars
```

## Cost Optimization

### Development Environment

- Use smaller task sizes (0.5 vCPU, 1 GB memory)
- Run single task per service
- Use shorter log retention (7 days)
- Delete unused images from ECR

### Production Environment

- Right-size tasks based on metrics
- Enable auto-scaling
- Use Fargate Savings Plans for predictable workloads
- Implement S3 lifecycle policies

## Security Best Practices

1. **Network Security**
   - All tasks in private subnets
   - ALB in public subnet as single entry point
   - Security groups with least privilege

2. **Data Security**
   - S3 encryption at rest (SSE-S3)
   - Enforce SSL/TLS for all connections
   - Use Secrets Manager for sensitive data

3. **Access Control**
   - IAM roles with least privilege
   - Cognito for user authentication
   - JWT tokens for service-to-service auth

4. **Monitoring**
   - Enable CloudWatch Logs
   - Set up CloudWatch Alarms
   - Regular security audits

## Multi-Zone Deployment

To deploy to both Zone A (dev) and Zone B (prod):

```bash
# Deploy to dev
export ENVIRONMENT=dev
./build-all.sh
cd terraform/environments/dev
terraform apply -var-file=terraform.tfvars

# Deploy to prod
export ENVIRONMENT=prod
./build-all.sh
cd terraform/environments/prod
terraform apply -var-file=terraform.tfvars
```

## Support

For issues or questions:
1. Check CloudWatch Logs
2. Review Terraform state
3. Verify AWS service quotas
4. Check AWS service health dashboard
