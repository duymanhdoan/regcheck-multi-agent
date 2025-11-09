# Prod Environment Variables

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

# VPC Variables
variable "vpc_cidr_primary" {
  description = "Primary CIDR block for VPC"
  type        = string
}

variable "vpc_cidr_secondary" {
  description = "Secondary CIDR block for VPC (for application tier)"
  type        = string
}

variable "public_subnet_cidr" {
  description = "CIDR block for public subnet (from primary range)"
  type        = string
}

variable "private_subnet_cidr" {
  description = "CIDR block for private subnet (from secondary range)"
  type        = string
}

variable "availability_zone" {
  description = "Availability zone for subnets"
  type        = string
  default     = "ap-southeast-1b"
}

# NLB Variables
variable "nlb_name" {
  description = "Name of the Network Load Balancer"
  type        = string
}

variable "nlb_enable_deletion_protection" {
  description = "Enable deletion protection for the NLB"
  type        = bool
  default     = true
}

variable "nlb_health_check_path" {
  description = "Health check path for the target group"
  type        = string
  default     = "/health"
}

variable "nlb_health_check_interval" {
  description = "Health check interval in seconds"
  type        = number
  default     = 30
}

variable "nlb_healthy_threshold" {
  description = "Number of consecutive health checks successes required"
  type        = number
  default     = 2
}

variable "nlb_unhealthy_threshold" {
  description = "Number of consecutive health check failures required"
  type        = number
  default     = 3
}

# S3 Variables
variable "s3_bucket_name" {
  description = "Name of the S3 bucket for file storage"
  type        = string
}

# Cognito Variables
variable "cognito_user_pool_name" {
  description = "Name of the Cognito User Pool"
  type        = string
}

variable "cognito_create_domain" {
  description = "Whether to create a Cognito User Pool domain"
  type        = bool
  default     = false
}

variable "cognito_domain_prefix" {
  description = "Domain prefix for Cognito hosted UI"
  type        = string
  default     = "internal-users-prod"
}

# ECS Variables
variable "ecr_repository_urls" {
  description = "Map of ECR repository URLs for each service"
  type        = map(string)
  default = {
    frontend     = ""
    agentgateway = ""
    application  = ""
    mcp_finance  = ""
    mcp_hr       = ""
    mcp_legal    = ""
  }
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}
