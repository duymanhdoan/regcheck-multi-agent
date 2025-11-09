# Quick Start Guide

Fast deployment guide for the Internal File Processing System.

## Prerequisites

```bash
# Install required tools
- AWS CLI
- Docker
- Terraform >= 1.0
```

## 5-Minute Deployment

### 1. Set Environment Variables

```bash
export AWS_ACCOUNT_ID=123456789012
export AWS_REGION=ap-southeast-1
export ENVIRONMENT=dev
```

### 2. Deploy Infrastructure

```bash
cd terraform/environments/dev
terraform init
terraform apply -var-file=terraform.tfvars -auto-approve
cd ../../..
```

### 3. Build and Push All Images

```bash
./build-all.sh
```

### 4. Deploy Services

```bash
# Update all ECS services
for service in frontend agentgateway application mcp-finance mcp-hr mcp-legal; do
  aws ecs update-service \
    --cluster ${ENVIRONMENT}-ecs-cluster \
    --service ${service}-service \
    --force-new-deployment \
    --region ${AWS_REGION}
done
```

### 5. Get Application URL

```bash
cd terraform/environments/dev
terraform output alb_dns_name
```

## Verify Deployment

```bash
# Get ALB DNS
ALB_DNS=$(cd terraform/environments/dev && terraform output -raw alb_dns_name)

# Test health endpoints
curl http://${ALB_DNS}/health
curl http://${ALB_DNS}/api/health
curl http://${ALB_DNS}/mcp/health
curl http://${ALB_DNS}/app/health
```

## Common Commands

### Build Single Service

```bash
cd <service-directory>
./build.sh
```

### View Logs

```bash
aws logs tail /ecs/dev/frontend --follow
```

### Scale Service

```bash
aws ecs update-service \
  --cluster dev-ecs-cluster \
  --service frontend-service \
  --desired-count 2
```

### Destroy Everything

```bash
cd terraform/environments/dev
terraform destroy -var-file=terraform.tfvars -auto-approve
```

## Service Ports

- Frontend: 8080
- AgentGateway API: 8080
- AgentGateway MCP: 8081
- Application: 8000
- MCP Servers: 8082

## Default Credentials

Create Cognito user:
```bash
USER_POOL_ID=$(cd terraform/environments/dev && terraform output -raw cognito_user_pool_id)

aws cognito-idp admin-create-user \
  --user-pool-id ${USER_POOL_ID} \
  --username admin@example.com \
  --user-attributes Name=email,Value=admin@example.com \
  --temporary-password Admin123! \
  --region ${AWS_REGION}
```

## Troubleshooting

**Services not starting?**
```bash
aws ecs describe-services \
  --cluster dev-ecs-cluster \
  --services frontend-service \
  --region ${AWS_REGION}
```

**Check task logs:**
```bash
aws logs tail /ecs/dev/frontend --follow
```

**Images not in ECR?**
```bash
aws ecr list-images --repository-name frontend --region ${AWS_REGION}
```

## Next Steps

- See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guide
- Configure Cognito users
- Upload sample data to S3
- Set up CloudWatch alarms
- Configure auto-scaling
