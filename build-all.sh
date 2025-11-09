#!/bin/bash

# Build and push all service Docker images to ECR

set -e

# Configuration
AWS_REGION="${AWS_REGION:-ap-southeast-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Building All Services${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if AWS_ACCOUNT_ID is set
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}Error: AWS_ACCOUNT_ID environment variable is not set${NC}"
    echo "Usage: AWS_ACCOUNT_ID=123456789012 ./build-all.sh"
    exit 1
fi

# Export variables for child scripts
export AWS_REGION
export AWS_ACCOUNT_ID
export IMAGE_TAG

# Track build status
FAILED_BUILDS=()

# Function to build a service
build_service() {
    local service_dir=$1
    local service_name=$2
    
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Building ${service_name}${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    if [ -f "${service_dir}/build.sh" ]; then
        cd "${service_dir}"
        if bash build.sh; then
            echo -e "${GREEN}✓ ${service_name} built successfully${NC}"
        else
            echo -e "${RED}✗ ${service_name} build failed${NC}"
            FAILED_BUILDS+=("${service_name}")
        fi
        cd - > /dev/null
    else
        echo -e "${YELLOW}⚠ No build.sh found for ${service_name}${NC}"
    fi
}

# Build all services
build_service "frontend" "Frontend (Langflow)"
build_service "agentgateway" "AgentGateway"
build_service "application" "Application"

# Build MCP servers
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Building MCP Servers${NC}"
echo -e "${BLUE}========================================${NC}"

if [ -f "mcp-servers/build.sh" ]; then
    cd mcp-servers
    
    for server_type in finance hr legal; do
        echo ""
        echo -e "${YELLOW}Building MCP ${server_type} server...${NC}"
        if bash build.sh ${server_type}; then
            echo -e "${GREEN}✓ MCP ${server_type} server built successfully${NC}"
        else
            echo -e "${RED}✗ MCP ${server_type} server build failed${NC}"
            FAILED_BUILDS+=("MCP ${server_type} server")
        fi
    done
    
    cd - > /dev/null
else
    echo -e "${YELLOW}⚠ No build.sh found for MCP servers${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Build Summary${NC}"
echo -e "${BLUE}========================================${NC}"

if [ ${#FAILED_BUILDS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All services built successfully!${NC}"
    echo ""
    echo -e "${GREEN}Images pushed to ECR:${NC}"
    echo -e "  - ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/frontend:${IMAGE_TAG}"
    echo -e "  - ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/agentgateway:${IMAGE_TAG}"
    echo -e "  - ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/application:${IMAGE_TAG}"
    echo -e "  - ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/mcp-finance-server:${IMAGE_TAG}"
    echo -e "  - ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/mcp-hr-server:${IMAGE_TAG}"
    echo -e "  - ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/mcp-legal-server:${IMAGE_TAG}"
    exit 0
else
    echo -e "${RED}✗ Some builds failed:${NC}"
    for service in "${FAILED_BUILDS[@]}"; do
        echo -e "  - ${service}"
    done
    exit 1
fi
