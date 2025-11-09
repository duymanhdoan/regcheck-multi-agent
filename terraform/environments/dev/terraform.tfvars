# Dev Environment Configuration Values

# Environment
environment = "dev"
region      = "ap-southeast-1"

# VPC Configuration
vpc_cidr_primary    = "10.0.0.0/16"
vpc_cidr_secondary  = "100.64.0.0/16"
public_subnet_cidr  = "10.0.1.0/24"
private_subnet_cidr = "100.64.0.0/20"
availability_zone   = "ap-southeast-1a"

# NLB Configuration (Network Load Balancer for single-AZ)
nlb_name                       = "dev-nlb-ap-southeast-1"
nlb_enable_deletion_protection = false
nlb_health_check_path          = "/health"
nlb_health_check_interval      = 30
nlb_healthy_threshold          = 2
nlb_unhealthy_threshold        = 3

# S3 Configuration
s3_bucket_name = "app-files-dev-ap-southeast-1"

# Cognito Configuration
cognito_user_pool_name = "dev-internal-users"
cognito_create_domain  = false
cognito_domain_prefix  = "internal-users-dev"

# ECS Configuration
# Note: Update these with actual ECR repository URLs after creating ECR repositories
ecr_repository_urls = {
  frontend     = "959750010280.dkr.ecr.ap-southeast-1.amazonaws.com/frontend"
  agentgateway = "959750010280.dkr.ecr.ap-southeast-1.amazonaws.com/agentgateway"
  application  = "959750010280.dkr.ecr.ap-southeast-1.amazonaws.com/application"
  mcp_finance  = "959750010280.dkr.ecr.ap-southeast-1.amazonaws.com/mcp-finance-server"
  mcp_hr       = "959750010280.dkr.ecr.ap-southeast-1.amazonaws.com/mcp-hr-server"
  mcp_legal    = "959750010280.dkr.ecr.ap-southeast-1.amazonaws.com/mcp-legal-server"
}

image_tag = "latest"
