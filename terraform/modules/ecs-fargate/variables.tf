variable "environment" {
  description = "Environment name (dev or prod)"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for Fargate tasks"
  type        = list(string)
}

variable "fargate_security_group_id" {
  description = "Security group ID for Fargate tasks"
  type        = string
}

variable "nlb_target_group_arn" {
  description = "ARN of the NLB target group for frontend service"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for file storage"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket for file storage"
  type        = string
}

variable "cognito_user_pool_id" {
  description = "ID of the Cognito User Pool"
  type        = string
}

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

variable "efs_file_system_id" {
  description = "ID of the EFS file system for Langflow persistent storage"
  type        = string
}

variable "efs_file_system_arn" {
  description = "ARN of the EFS file system for Langflow persistent storage"
  type        = string
}

variable "efs_access_point_id" {
  description = "ID of the EFS access point for Langflow"
  type        = string
}

variable "efs_access_point_arn" {
  description = "ARN of the EFS access point for Langflow"
  type        = string
}
