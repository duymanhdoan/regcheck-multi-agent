#!/bin/bash

# Deploy Infrastructure to Zone A (Dev Environment)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Deploying to Zone A (Dev Environment)${NC}"
echo -e "${BLUE}========================================${NC}"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check Terraform
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: Terraform is not installed${NC}"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials are not configured${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION="${AWS_REGION:-ap-southeast-1}"

echo -e "${GREEN}AWS Account ID: ${AWS_ACCOUNT_ID}${NC}"
echo -e "${GREEN}AWS Region: ${AWS_REGION}${NC}"

# Export for child processes
export AWS_ACCOUNT_ID
export AWS_REGION
export IMAGE_TAG="${IMAGE_TAG:-latest}"

# Step 1: Initialize Terraform
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 1: Initialize Terraform${NC}"
echo -e "${BLUE}========================================${NC}"

cd terraform/environments/dev

if [ ! -d ".terraform" ]; then
    echo -e "${YELLOW}Running terraform init...${NC}"
    terraform init
    echo -e "${GREEN}✓ Terraform initialized${NC}"
else
    echo -e "${GREEN}✓ Terraform already initialized${NC}"
fi

# Step 2: Update terraform.tfvars with AWS Account ID
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 2: Update Configuration${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "${YELLOW}Updating ECR repository URLs in terraform.tfvars...${NC}"

# Create a backup
cp terraform.tfvars terraform.tfvars.backup

# Update ECR URLs
sed -i.bak "s/<AWS_ACCOUNT_ID>/${AWS_ACCOUNT_ID}/g" terraform.tfvars
rm terraform.tfvars.bak

echo -e "${GREEN}✓ Configuration updated${NC}"

# Step 3: Terraform Plan
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 3: Review Infrastructure Plan${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "${YELLOW}Running terraform plan...${NC}"
terraform plan -var-file=terraform.tfvars -out=tfplan

echo ""
echo -e "${YELLOW}Review the plan above. Do you want to proceed with deployment? (yes/no)${NC}"
read -r PROCEED

if [ "$PROCEED" != "yes" ]; then
    echo -e "${YELLOW}Deployment cancelled${NC}"
    exit 0
fi

# Step 4: Terraform Apply
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 4: Deploy Infrastructure${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "${YELLOW}Applying Terraform configuration...${NC}"
terraform apply tfplan

echo -e "${GREEN}✓ Infrastructure deployed${NC}"

# Get outputs
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Infrastructure Outputs${NC}"
echo -e "${BLUE}========================================${NC}"

terraform output

# Save outputs to file
terraform output -json > outputs.json

# Step 5: Build and Push Container Images
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 5: Build and Push Container Images${NC}"
echo -e "${BLUE}========================================${NC}"

cd ../../..

echo -e "${YELLOW}Building all service images...${NC}"
./build-all.sh

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All images built and pushed${NC}"
else
    echo -e "${RED}✗ Image build failed${NC}"
    exit 1
fi

# Step 6: Deploy Services to ECS
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 6: Deploy Services to ECS${NC}"
echo -e "${BLUE}========================================${NC}"

CLUSTER_NAME="dev-ecs-cluster"
SERVICES=("frontend" "agentgateway" "application" "mcp-finance" "mcp-hr" "mcp-legal")

for service in "${SERVICES[@]}"; do
    echo -e "${YELLOW}Deploying ${service}-service...${NC}"
    
    aws ecs update-service \
        --cluster ${CLUSTER_NAME} \
        --service ${service}-service \
        --force-new-deployment \
        --region ${AWS_REGION} \
        > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ${service}-service deployment initiated${NC}"
    else
        echo -e "${RED}✗ ${service}-service deployment failed${NC}"
    fi
done

# Step 7: Wait for Services to Stabilize
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 7: Waiting for Services${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "${YELLOW}Waiting for services to stabilize (this may take a few minutes)...${NC}"

for service in "${SERVICES[@]}"; do
    echo -e "${YELLOW}Waiting for ${service}-service...${NC}"
    
    aws ecs wait services-stable \
        --cluster ${CLUSTER_NAME} \
        --services ${service}-service \
        --region ${AWS_REGION}
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ${service}-service is stable${NC}"
    else
        echo -e "${YELLOW}⚠ ${service}-service stabilization timeout (check manually)${NC}"
    fi
done

# Step 8: Verify Deployment
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 8: Verify Deployment${NC}"
echo -e "${BLUE}========================================${NC}"

# Get NLB DNS name
cd terraform/environments/dev
NLB_DNS=$(terraform output -raw nlb_dns_name 2>/dev/null || echo "")

if [ -n "$NLB_DNS" ]; then
    echo -e "${GREEN}Network Load Balancer DNS: ${NLB_DNS}${NC}"
    echo ""
    echo -e "${YELLOW}Testing health endpoints...${NC}"
    
    # Test health endpoints
    ENDPOINTS=("/health" "/api/health" "/mcp/health" "/app/health")
    
    for endpoint in "${ENDPOINTS[@]}"; do
        echo -e "${YELLOW}Testing http://${NLB_DNS}${endpoint}${NC}"
        
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${NLB_DNS}${endpoint}" || echo "000")
        
        if [ "$HTTP_CODE" = "200" ]; then
            echo -e "${GREEN}✓ ${endpoint} is healthy (HTTP ${HTTP_CODE})${NC}"
        else
            echo -e "${YELLOW}⚠ ${endpoint} returned HTTP ${HTTP_CODE}${NC}"
        fi
    done
else
    echo -e "${YELLOW}⚠ Could not retrieve NLB DNS name${NC}"
fi

cd ../../..

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Deployment Summary${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "${GREEN}✓ Infrastructure deployed to Zone A (dev)${NC}"
echo -e "${GREEN}✓ Container images built and pushed${NC}"
echo -e "${GREEN}✓ Services deployed to ECS${NC}"

if [ -n "$NLB_DNS" ]; then
    echo ""
    echo -e "${GREEN}Access your application at: http://${NLB_DNS}${NC}"
fi

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Create Cognito users"
echo -e "  2. Upload sample data to S3"
echo -e "  3. Configure CloudWatch alarms"
echo -e "  4. Set up monitoring dashboards"

echo ""
echo -e "${GREEN}Deployment complete!${NC}"
