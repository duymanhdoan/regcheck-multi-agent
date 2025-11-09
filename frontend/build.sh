#!/bin/bash

# Build and push Frontend (Langflow) Docker image to ECR

set -e

# Configuration
SERVICE_NAME="frontend"
AWS_REGION="${AWS_REGION:-ap-southeast-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID}"
ECR_REPOSITORY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${SERVICE_NAME}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building and pushing ${SERVICE_NAME} service${NC}"

# Check if AWS_ACCOUNT_ID is set
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}Error: AWS_ACCOUNT_ID environment variable is not set${NC}"
    echo "Usage: AWS_ACCOUNT_ID=123456789012 ./build.sh"
    exit 1
fi

# Authenticate with ECR
echo -e "${YELLOW}Authenticating with ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${ECR_REPOSITORY}

# Build Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t ${SERVICE_NAME}:${IMAGE_TAG} .

# Tag image for ECR
echo -e "${YELLOW}Tagging image...${NC}"
docker tag ${SERVICE_NAME}:${IMAGE_TAG} ${ECR_REPOSITORY}:${IMAGE_TAG}

# Push image to ECR
echo -e "${YELLOW}Pushing image to ECR...${NC}"
docker push ${ECR_REPOSITORY}:${IMAGE_TAG}

echo -e "${GREEN}Successfully built and pushed ${SERVICE_NAME}:${IMAGE_TAG}${NC}"
echo -e "${GREEN}Image: ${ECR_REPOSITORY}:${IMAGE_TAG}${NC}"
