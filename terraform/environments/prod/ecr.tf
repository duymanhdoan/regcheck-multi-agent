# ECR Repositories for Prod Environment

module "ecr" {
  source = "../../modules/ecr"

  environment = var.environment

  repository_names = [
    "frontend",
    "agentgateway",
    "application",
    "mcp-finance-server",
    "mcp-hr-server",
    "mcp-legal-server"
  ]

  image_tag_mutability = "IMMUTABLE"  # Immutable tags for production
  scan_on_push         = true

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = "Internal-File-Processing"
  }
}

# Output ECR repository URLs for easy reference
output "ecr_repository_urls" {
  description = "ECR repository URLs"
  value       = module.ecr.repository_urls
}
