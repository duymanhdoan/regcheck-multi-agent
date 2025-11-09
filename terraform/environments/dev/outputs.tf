# Dev Environment Outputs

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_primary" {
  description = "Primary CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_primary
}

output "vpc_cidr_secondary" {
  description = "Secondary CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_secondary
}

output "public_subnet_id" {
  description = "ID of the public subnet"
  value       = module.vpc.public_subnet_id
}

output "private_subnet_id" {
  description = "ID of the private subnet"
  value       = module.vpc.private_subnet_id
}

# Security Group Outputs
output "fargate_tasks_security_group_id" {
  description = "ID of the Fargate tasks security group"
  value       = module.security_groups.fargate_tasks_security_group_id
}

# NLB Outputs
output "nlb_dns_name" {
  description = "DNS name of the Network Load Balancer"
  value       = module.nlb.nlb_dns_name
}

output "nlb_arn" {
  description = "ARN of the Network Load Balancer"
  value       = module.nlb.nlb_arn
}

output "nlb_zone_id" {
  description = "Zone ID of the Network Load Balancer"
  value       = module.nlb.nlb_zone_id
}

output "frontend_target_group_arn" {
  description = "ARN of the frontend target group"
  value       = module.nlb.frontend_target_group_arn
}

# S3 Outputs
output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.s3.bucket_arn
}

# Cognito Outputs
output "cognito_user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = module.cognito.user_pool_id
}

output "cognito_user_pool_arn" {
  description = "ARN of the Cognito User Pool"
  value       = module.cognito.user_pool_arn
}

output "cognito_user_pool_client_id" {
  description = "ID of the Cognito User Pool Client"
  value       = module.cognito.user_pool_client_id
}

output "cognito_user_pool_endpoint" {
  description = "Endpoint of the Cognito User Pool"
  value       = module.cognito.user_pool_endpoint
}

# ECS Outputs
output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = module.ecs_fargate.ecs_cluster_id
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs_fargate.ecs_cluster_name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = module.ecs_fargate.ecs_cluster_arn
}

output "service_discovery_namespace_name" {
  description = "Name of the service discovery namespace"
  value       = module.ecs_fargate.service_discovery_namespace_name
}

# Service Names
output "frontend_service_name" {
  description = "Name of the frontend ECS service"
  value       = module.ecs_fargate.frontend_service_name
}

output "agentgateway_service_name" {
  description = "Name of the agentgateway ECS service"
  value       = module.ecs_fargate.agentgateway_service_name
}

output "application_service_name" {
  description = "Name of the application ECS service"
  value       = module.ecs_fargate.application_service_name
}

output "mcp_finance_service_name" {
  description = "Name of the MCP finance ECS service"
  value       = module.ecs_fargate.mcp_finance_service_name
}

output "mcp_hr_service_name" {
  description = "Name of the MCP HR ECS service"
  value       = module.ecs_fargate.mcp_hr_service_name
}

output "mcp_legal_service_name" {
  description = "Name of the MCP legal ECS service"
  value       = module.ecs_fargate.mcp_legal_service_name
}

# Application Access
output "application_url" {
  description = "URL to access the application"
  value       = "http://${module.nlb.nlb_dns_name}"
}
