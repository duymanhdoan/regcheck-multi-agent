output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "service_discovery_namespace_id" {
  description = "ID of the service discovery namespace"
  value       = aws_service_discovery_private_dns_namespace.main.id
}

output "service_discovery_namespace_name" {
  description = "Name of the service discovery namespace"
  value       = aws_service_discovery_private_dns_namespace.main.name
}

output "service_discovery_namespace_arn" {
  description = "ARN of the service discovery namespace"
  value       = aws_service_discovery_private_dns_namespace.main.arn
}

# Service outputs
output "frontend_service_name" {
  description = "Name of the frontend ECS service"
  value       = aws_ecs_service.frontend.name
}

output "agentgateway_service_name" {
  description = "Name of the agentgateway ECS service"
  value       = aws_ecs_service.agentgateway.name
}

output "application_service_name" {
  description = "Name of the application ECS service"
  value       = aws_ecs_service.application.name
}

output "mcp_finance_service_name" {
  description = "Name of the MCP finance ECS service"
  value       = aws_ecs_service.mcp_finance.name
}

output "mcp_hr_service_name" {
  description = "Name of the MCP HR ECS service"
  value       = aws_ecs_service.mcp_hr.name
}

output "mcp_legal_service_name" {
  description = "Name of the MCP legal ECS service"
  value       = aws_ecs_service.mcp_legal.name
}

# Task definition outputs
output "frontend_task_definition_arn" {
  description = "ARN of the frontend task definition"
  value       = aws_ecs_task_definition.frontend.arn
}

output "agentgateway_task_definition_arn" {
  description = "ARN of the agentgateway task definition"
  value       = aws_ecs_task_definition.agentgateway.arn
}

output "application_task_definition_arn" {
  description = "ARN of the application task definition"
  value       = aws_ecs_task_definition.application.arn
}

output "mcp_finance_task_definition_arn" {
  description = "ARN of the MCP finance task definition"
  value       = aws_ecs_task_definition.mcp_finance.arn
}

output "mcp_hr_task_definition_arn" {
  description = "ARN of the MCP HR task definition"
  value       = aws_ecs_task_definition.mcp_hr.arn
}

output "mcp_legal_task_definition_arn" {
  description = "ARN of the MCP legal task definition"
  value       = aws_ecs_task_definition.mcp_legal.arn
}

# IAM role outputs
output "task_execution_role_arn" {
  description = "ARN of the task execution role"
  value       = aws_iam_role.task_execution_role.arn
}

output "frontend_task_role_arn" {
  description = "ARN of the frontend task role"
  value       = aws_iam_role.frontend_task_role.arn
}

output "agentgateway_task_role_arn" {
  description = "ARN of the agentgateway task role"
  value       = aws_iam_role.agentgateway_task_role.arn
}

output "application_task_role_arn" {
  description = "ARN of the application task role"
  value       = aws_iam_role.application_task_role.arn
}

output "mcp_finance_task_role_arn" {
  description = "ARN of the MCP finance task role"
  value       = aws_iam_role.mcp_finance_task_role.arn
}

output "mcp_hr_task_role_arn" {
  description = "ARN of the MCP HR task role"
  value       = aws_iam_role.mcp_hr_task_role.arn
}

output "mcp_legal_task_role_arn" {
  description = "ARN of the MCP legal task role"
  value       = aws_iam_role.mcp_legal_task_role.arn
}

# EFS outputs
# EFS outputs removed - now managed by dedicated EFS module
