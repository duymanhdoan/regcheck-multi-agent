# EFS Module Outputs

output "efs_file_system_id" {
  description = "ID of the EFS file system"
  value       = aws_efs_file_system.langflow.id
}

output "efs_file_system_arn" {
  description = "ARN of the EFS file system"
  value       = aws_efs_file_system.langflow.arn
}

output "efs_access_point_id" {
  description = "ID of the EFS access point"
  value       = aws_efs_access_point.langflow.id
}

output "efs_access_point_arn" {
  description = "ARN of the EFS access point"
  value       = aws_efs_access_point.langflow.arn
}
