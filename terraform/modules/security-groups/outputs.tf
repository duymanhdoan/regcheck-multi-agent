output "fargate_tasks_security_group_id" {
  description = "ID of the Fargate tasks security group"
  value       = aws_security_group.fargate_tasks.id
}

output "efs_security_group_id" {
  description = "ID of the EFS security group"
  value       = aws_security_group.efs.id
}
