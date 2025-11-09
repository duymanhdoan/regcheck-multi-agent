# Prod Environment Configuration Values

# Environment
environment = "prod"
region      = "ap-southeast-1"

# VPC Configuration
vpc_cidr_primary    = "10.1.0.0/16"
vpc_cidr_secondary  = "100.65.0.0/16"
public_subnet_cidr  = "10.1.1.0/24"
private_subnet_cidr = "100.65.0.0/20"
availability_zone   = "ap-southeast-1b"

# NLB Configuration (Network Load Balancer for single-AZ)
nlb_name                       = "prod-nlb-ap-southeast-1"
nlb_enable_deletion_protection = true
nlb_health_check_path          = "/health"
nlb_health_check_interval      = 30
nlb_healthy_threshold          = 2
nlb_unhealthy_threshold        = 3

# S3 Configuration
s3_bucket_name = "app-files-prod-ap-southeast-1"

# Cognito Configuration
cognito_user_pool_name = "prod-internal-users"
cognito_create_domain  = false
cognito_domain_prefix  = "internal-users-prod"

# ECS Configuration
# Note: Update these with actual ECR repository URLs after creating ECR repositories
ecr_repository_urls = {
  frontend     = "<AWS_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/frontend"
  agentgateway = "<AWS_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/agentgateway"
  application  = "<AWS_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/application"
  mcp_finance  = "<AWS_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/mcp-finance-server"
  mcp_hr       = "<AWS_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/mcp-hr-server"
  mcp_legal    = "<AWS_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/mcp-legal-server"
}

image_tag = "latest"
