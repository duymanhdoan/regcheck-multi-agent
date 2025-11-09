# Langflow Frontend - Quick Start Guide

## Prerequisites

- AWS CLI configured with appropriate credentials
- Docker installed and running
- Terraform installed (for infrastructure deployment)
- Access to AWS account with necessary permissions

## Quick Deployment (5 Steps)

### Step 1: Build Docker Image

```bash
cd frontend
./build.sh dev
```

This will:
- Authenticate with ECR
- Build the Langflow image with custom components
- Push to ECR repository

**Expected Output**:
```
Building Docker image...
Pushing image to ECR...
Build and push completed successfully!
Image: <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/frontend:latest
```

### Step 2: Deploy Infrastructure

```bash
cd ../terraform/environments/dev
terraform init
terraform apply
```

**What Gets Created**:
- EFS file system for persistent storage
- EFS mount targets in private subnets
- EFS access point for Langflow
- Updated ECS task definition (1 vCPU, 2 GB, port 7860)
- Updated ALB target group (port 7860, stickiness enabled)
- IAM policies for EFS access

**Expected Duration**: 5-10 minutes

### Step 3: Wait for Service to Stabilize

```bash
aws ecs wait services-stable \
  --cluster dev-ecs-cluster \
  --services frontend-service \
  --region ap-southeast-1
```

### Step 4: Get ALB URL

```bash
aws elbv2 describe-load-balancers \
  --names dev-alb-ap-southeast-1 \
  --query 'LoadBalancers[0].DNSName' \
  --output text \
  --region ap-southeast-1
```

### Step 5: Access Langflow

Open your browser and navigate to:
```
http://<alb-dns-name>
```

You should see the Langflow UI!

## Verify Custom Components

1. In Langflow UI, click on "Components" in the sidebar
2. Look for custom components:
   - **AgentGateway API** (cloud icon)
   - **S3 File Operations** (database icon)
   - **MCP Server Client** (server icon)

## Create Your First Flow

### Example: File Upload to S3

1. Drag **S3 File Operations** component to canvas
2. Configure:
   - Bucket Name: `app-files-dev-ap-southeast-1`
   - Operation: `upload`
   - File Path: `/path/to/local/file.txt`
   - S3 Key: `uploads/test/file.txt`
3. Click "Run" to execute

### Example: Call AgentGateway API

1. Drag **AgentGateway API** component to canvas
2. Configure:
   - API URL: `http://agentgateway-service.dev.local:8080`
   - Endpoint: `/api/status/test-123`
   - Method: `GET`
3. Connect JWT token (if required)
4. Click "Run" to execute

### Example: Query MCP Server

1. Drag **MCP Server Client** component to canvas
2. Configure:
   - AgentGateway URL: `http://agentgateway-service.dev.local:8081`
   - Server Type: `finance`
   - Method: `tools/list`
3. Click "Run" to see available tools

## Troubleshooting

### Issue: Container Won't Start

**Check logs**:
```bash
aws logs tail /ecs/dev/frontend --follow --region ap-southeast-1
```

**Common causes**:
- ECR image not found
- EFS mount failed
- IAM permissions missing

### Issue: Health Check Failing

**Check target health**:
```bash
aws elbv2 describe-target-health \
  --target-group-arn <arn> \
  --region ap-southeast-1
```

**Common causes**:
- Langflow not listening on port 7860
- Security group blocking traffic
- Container startup taking too long

### Issue: Can't Access via ALB

**Check security groups**:
```bash
# ALB should allow inbound on port 80
# Fargate tasks should allow inbound from ALB on port 7860
```

**Check ALB listener**:
```bash
aws elbv2 describe-listeners \
  --load-balancer-arn <arn> \
  --region ap-southeast-1
```

### Issue: Custom Components Not Showing

**Verify components are in image**:
```bash
# Exec into container
aws ecs execute-command \
  --cluster dev-ecs-cluster \
  --task <task-id> \
  --container frontend \
  --interactive \
  --command "/bin/bash" \
  --region ap-southeast-1

# Inside container
ls -la /app/langflow_components/
echo $LANGFLOW_COMPONENTS_PATH
```

### Issue: EFS Mount Failed

**Check mount targets**:
```bash
aws efs describe-mount-targets \
  --file-system-id <fs-id> \
  --region ap-southeast-1
```

**Check security group**:
- Must allow NFS traffic (port 2049) from Fargate security group

## Useful Commands

### View Service Status
```bash
aws ecs describe-services \
  --cluster dev-ecs-cluster \
  --services frontend-service \
  --region ap-southeast-1
```

### View Running Tasks
```bash
aws ecs list-tasks \
  --cluster dev-ecs-cluster \
  --service-name frontend-service \
  --region ap-southeast-1
```

### Force New Deployment
```bash
aws ecs update-service \
  --cluster dev-ecs-cluster \
  --service frontend-service \
  --force-new-deployment \
  --region ap-southeast-1
```

### View CloudWatch Logs
```bash
aws logs tail /ecs/dev/frontend --follow --region ap-southeast-1
```

### Check EFS File System
```bash
aws efs describe-file-systems \
  --region ap-southeast-1
```

### Scale Service Manually
```bash
aws ecs update-service \
  --cluster dev-ecs-cluster \
  --service frontend-service \
  --desired-count 2 \
  --region ap-southeast-1
```

## Production Deployment

For production, use the same steps but with `prod` environment:

```bash
# Build and push
cd frontend
./build.sh prod

# Deploy infrastructure
cd ../terraform/environments/prod
terraform apply

# Get ALB URL
aws elbv2 describe-load-balancers \
  --names prod-alb-ap-southeast-1 \
  --query 'LoadBalancers[0].DNSName' \
  --output text \
  --region ap-southeast-1
```

## Next Steps

1. **Create Flows**: Build workflows using custom components
2. **Test Integration**: Verify backend connectivity
3. **Configure Authentication**: Set up Cognito integration
4. **Monitor Performance**: Watch CloudWatch metrics
5. **Optimize Costs**: Adjust auto scaling settings

## Support Resources

- **Langflow Docs**: https://docs.langflow.org/
- **Custom Components**: See `langflow_components/README.md`
- **Full Documentation**: See `README.md`
- **Deployment Details**: See `DEPLOYMENT_SUMMARY.md`

## Cost Estimate

**Dev Environment** (1 task running 24/7):
- Fargate: ~$30/month
- EFS: ~$5/month
- ALB: ~$20/month
- **Total**: ~$55/month

**Prod Environment** (avg 3 tasks):
- Fargate: ~$90/month
- EFS: ~$10/month
- ALB: ~$20/month
- **Total**: ~$120/month

## Security Notes

- Frontend runs in private subnet (no public IP)
- Access only via ALB
- EFS encrypted at rest and in transit
- IAM roles provide AWS credentials (no hardcoded secrets)
- Session stickiness enabled for user experience

---

**Need Help?** Check CloudWatch logs first, then review the troubleshooting section above.
