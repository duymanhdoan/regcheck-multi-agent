output "s3_endpoint_id" {
  description = "ID of the S3 Gateway Endpoint"
  value       = aws_vpc_endpoint.s3.id
}

output "ecr_api_endpoint_id" {
  description = "ID of the ECR API Interface Endpoint"
  value       = aws_vpc_endpoint.ecr_api.id
}

output "ecr_dkr_endpoint_id" {
  description = "ID of the ECR DKR Interface Endpoint"
  value       = aws_vpc_endpoint.ecr_dkr.id
}

output "logs_endpoint_id" {
  description = "ID of the CloudWatch Logs Interface Endpoint"
  value       = aws_vpc_endpoint.logs.id
}
