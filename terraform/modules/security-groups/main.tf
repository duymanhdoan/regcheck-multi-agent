# Fargate Task Security Group
resource "aws_security_group" "fargate_tasks" {
  name        = "${var.environment}-fargate-tasks-sg"
  description = "Security group for Fargate tasks"
  vpc_id      = var.vpc_id

  # Allow inbound HTTP from NLB (NLB passes through source IP, so allow from VPC CIDR)
  ingress {
    description = "HTTP from NLB/Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow inbound on port 7860 for Langflow from NLB
  ingress {
    description = "Langflow from NLB/Internet"
    from_port   = 7860
    to_port     = 7860
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow inbound on port 8000 from same security group (application service)
  ingress {
    description = "Application service port from tasks"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    self        = true
  }

  # Allow inbound on port 8080 from same security group (agentgateway API, MCP servers)
  ingress {
    description = "AgentGateway API and MCP servers from tasks"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    self        = true
  }

  # Allow inbound on port 8081 from same security group (agentgateway MCP)
  ingress {
    description = "AgentGateway MCP from tasks"
    from_port   = 8081
    to_port     = 8081
    protocol    = "tcp"
    self        = true
  }

  # Allow all traffic from same security group for task-to-task communication
  ingress {
    description = "All traffic from same security group"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }

  # Allow all outbound traffic (for ECR, S3, AWS APIs)
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.environment}-fargate-tasks-sg"
    Environment = var.environment
  }
}

# EFS Security Group
resource "aws_security_group" "efs" {
  name        = "${var.environment}-efs-sg"
  description = "Security group for EFS mount targets"
  vpc_id      = var.vpc_id

  # Allow NFS traffic from Fargate tasks
  ingress {
    description     = "NFS from Fargate tasks"
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.fargate_tasks.id]
  }

  # Allow all outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.environment}-efs-sg"
    Environment = var.environment
  }
}
