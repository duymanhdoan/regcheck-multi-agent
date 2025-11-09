# S3 Gateway Endpoint for private S3 access
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [var.private_route_table_id]

  tags = {
    Name        = "${var.environment}-s3-endpoint"
    Environment = var.environment
  }
}

# ECR API Interface Endpoint for pulling container images
resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [var.private_subnet_id]
  security_group_ids  = [var.fargate_security_group_id]
  private_dns_enabled = true

  tags = {
    Name        = "${var.environment}-ecr-api-endpoint"
    Environment = var.environment
  }
}

# ECR DKR Interface Endpoint for Docker registry access
resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [var.private_subnet_id]
  security_group_ids  = [var.fargate_security_group_id]
  private_dns_enabled = true

  tags = {
    Name        = "${var.environment}-ecr-dkr-endpoint"
    Environment = var.environment
  }
}

# CloudWatch Logs Interface Endpoint for log streaming
resource "aws_vpc_endpoint" "logs" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.region}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [var.private_subnet_id]
  security_group_ids  = [var.fargate_security_group_id]
  private_dns_enabled = true

  tags = {
    Name        = "${var.environment}-logs-endpoint"
    Environment = var.environment
  }
}
