# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.environment}-ecs-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "${var.environment}-ecs-cluster"
    Environment = var.environment
  }
}

# AWS Cloud Map namespace for service discovery
resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "${var.environment}.local"
  description = "Private DNS namespace for ${var.environment} ECS services"
  vpc         = var.vpc_id

  tags = {
    Name        = "${var.environment}-service-discovery"
    Environment = var.environment
  }
}

# ============================================================================
# EFS File System for Langflow Persistent Storage
# ============================================================================
# Note: EFS resources are now managed by the dedicated EFS module
# ============================================================================
# IAM Roles and Policies
# ============================================================================

# Task Execution Role (used by all services)
resource "aws_iam_role" "task_execution_role" {
  name = "${var.environment}-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.environment}-ecs-task-execution-role"
    Environment = var.environment
  }
}

# Attach AWS managed policy for ECS task execution
resource "aws_iam_role_policy_attachment" "task_execution_role_policy" {
  role       = aws_iam_role.task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Frontend Task Role
resource "aws_iam_role" "frontend_task_role" {
  name = "${var.environment}-frontend-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.environment}-frontend-task-role"
    Environment = var.environment
  }
}

# Frontend S3 PutObject policy
resource "aws_iam_role_policy" "frontend_s3_policy" {
  name = "${var.environment}-frontend-s3-policy"
  role = aws_iam_role.frontend_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${var.s3_bucket_arn}/uploads/*"
      }
    ]
  })
}

# Frontend EFS access policy
resource "aws_iam_role_policy" "frontend_efs_policy" {
  name = "${var.environment}-frontend-efs-policy"
  role = aws_iam_role.frontend_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "elasticfilesystem:ClientMount",
          "elasticfilesystem:ClientWrite",
          "elasticfilesystem:ClientRootAccess"
        ]
        Resource = var.efs_file_system_arn
        Condition = {
          StringEquals = {
            "elasticfilesystem:AccessPointArn" = var.efs_access_point_arn
          }
        }
      }
    ]
  })
}

# AgentGateway Task Role
resource "aws_iam_role" "agentgateway_task_role" {
  name = "${var.environment}-agentgateway-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.environment}-agentgateway-task-role"
    Environment = var.environment
  }
}

# Application Task Role
resource "aws_iam_role" "application_task_role" {
  name = "${var.environment}-application-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.environment}-application-task-role"
    Environment = var.environment
  }
}

# Application S3 GetObject and PutObject policy
resource "aws_iam_role_policy" "application_s3_policy" {
  name = "${var.environment}-application-s3-policy"
  role = aws_iam_role.application_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "${var.s3_bucket_arn}/uploads/*",
          "${var.s3_bucket_arn}/processed/*",
          "${var.s3_bucket_arn}/temp/*"
        ]
      }
    ]
  })
}

# MCP Finance Server Task Role
resource "aws_iam_role" "mcp_finance_task_role" {
  name = "${var.environment}-mcp-finance-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.environment}-mcp-finance-task-role"
    Environment = var.environment
  }
}

# MCP Finance S3 GetObject policy
resource "aws_iam_role_policy" "mcp_finance_s3_policy" {
  name = "${var.environment}-mcp-finance-s3-policy"
  role = aws_iam_role.mcp_finance_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${var.s3_bucket_arn}/finance/*"
      }
    ]
  })
}

# MCP HR Server Task Role
resource "aws_iam_role" "mcp_hr_task_role" {
  name = "${var.environment}-mcp-hr-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.environment}-mcp-hr-task-role"
    Environment = var.environment
  }
}

# MCP HR S3 GetObject policy
resource "aws_iam_role_policy" "mcp_hr_s3_policy" {
  name = "${var.environment}-mcp-hr-s3-policy"
  role = aws_iam_role.mcp_hr_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${var.s3_bucket_arn}/hr/*"
      }
    ]
  })
}

# MCP Legal Server Task Role
resource "aws_iam_role" "mcp_legal_task_role" {
  name = "${var.environment}-mcp-legal-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.environment}-mcp-legal-task-role"
    Environment = var.environment
  }
}

# MCP Legal S3 GetObject policy
resource "aws_iam_role_policy" "mcp_legal_s3_policy" {
  name = "${var.environment}-mcp-legal-s3-policy"
  role = aws_iam_role.mcp_legal_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${var.s3_bucket_arn}/legal/*"
      }
    ]
  })
}


# ============================================================================
# CloudWatch Log Groups
# ============================================================================

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${var.environment}/frontend"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.environment}-frontend-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "agentgateway" {
  name              = "/ecs/${var.environment}/agentgateway"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.environment}-agentgateway-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "application" {
  name              = "/ecs/${var.environment}/application"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.environment}-application-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "mcp_finance" {
  name              = "/ecs/${var.environment}/mcp-finance"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.environment}-mcp-finance-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "mcp_hr" {
  name              = "/ecs/${var.environment}/mcp-hr"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.environment}-mcp-hr-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "mcp_legal" {
  name              = "/ecs/${var.environment}/mcp-legal"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.environment}-mcp-legal-logs"
    Environment = var.environment
  }
}

# ============================================================================
# ECS Task Definitions
# ============================================================================

# Frontend Task Definition (1 vCPU, 2 GB) - Langflow
resource "aws_ecs_task_definition" "frontend" {
  family                   = "${var.environment}-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024" # 1 vCPU
  memory                   = "2048" # 2 GB
  execution_role_arn       = aws_iam_role.task_execution_role.arn
  task_role_arn            = aws_iam_role.frontend_task_role.arn

  # EFS Volume for persistent Langflow data
  volume {
    name = "langflow-data"

    efs_volume_configuration {
      file_system_id          = var.efs_file_system_id
      transit_encryption      = "ENABLED"
      transit_encryption_port = 2049
      authorization_config {
        access_point_id = var.efs_access_point_id
        iam             = "ENABLED"
      }
    }
  }

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = var.ecr_repository_urls["frontend"] != "" ? "${var.ecr_repository_urls["frontend"]}:${var.image_tag}" : "langflowai/langflow:latest"
      essential = true

      portMappings = [
        {
          containerPort = 7860
          protocol      = "tcp"
        }
      ]

      mountPoints = [
        {
          sourceVolume  = "langflow-data"
          containerPath = "/app/langflow"
          readOnly      = false
        }
      ]

      environment = [
        {
          name  = "LANGFLOW_DATABASE_URL"
          value = "sqlite:////app/langflow/langflow.db"
        },
        {
          name  = "LANGFLOW_CONFIG_DIR"
          value = "/app/langflow"
        },
        {
          name  = "LANGFLOW_LOG_LEVEL"
          value = "INFO"
        },
        {
          name  = "LANGFLOW_HOST"
          value = "0.0.0.0"
        },
        {
          name  = "LANGFLOW_PORT"
          value = "7860"
        },
        {
          name  = "LANGFLOW_BACKEND_URL"
          value = "http://agentgateway-service.${var.environment}.local:8080"
        },
        {
          name  = "AWS_REGION"
          value = var.region
        },
        {
          name  = "S3_BUCKET_NAME"
          value = var.s3_bucket_name
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.frontend.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name        = "${var.environment}-frontend-task"
    Environment = var.environment
  }
}

# AgentGateway Task Definition (0.5 vCPU, 1 GB)
resource "aws_ecs_task_definition" "agentgateway" {
  family                   = "${var.environment}-agentgateway"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"  # 0.5 vCPU
  memory                   = "1024" # 1 GB
  execution_role_arn       = aws_iam_role.task_execution_role.arn
  task_role_arn            = aws_iam_role.agentgateway_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "agentgateway"
      image     = var.ecr_repository_urls["agentgateway"] != "" ? "${var.ecr_repository_urls["agentgateway"]}:${var.image_tag}" : "nginx:latest"
      essential = true

      portMappings = [
        {
          containerPort = 8080
          protocol      = "tcp"
        },
        {
          containerPort = 8081
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "SERVICE_NAME"
          value = "agentgateway"
        },
        {
          name  = "API_PORT"
          value = "8080"
        },
        {
          name  = "MCP_PORT"
          value = "8081"
        },
        {
          name  = "AWS_REGION"
          value = var.region
        },
        {
          name  = "COGNITO_USER_POOL_ID"
          value = var.cognito_user_pool_id
        },
        {
          name  = "COGNITO_REGION"
          value = var.region
        },
        {
          name  = "RBAC_ENABLED"
          value = "true"
        },
        {
          name  = "DEPARTMENT_ISOLATION"
          value = "true"
        },
        {
          name  = "APPLICATION_SERVICE_URL"
          value = "http://application-service.${var.environment}.local:8000"
        },
        {
          name  = "MCP_FINANCE_URL"
          value = "http://mcp-finance-service.${var.environment}.local:8080"
        },
        {
          name  = "MCP_HR_URL"
          value = "http://mcp-hr-service.${var.environment}.local:8080"
        },
        {
          name  = "MCP_LEGAL_URL"
          value = "http://mcp-legal-service.${var.environment}.local:8080"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.agentgateway.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name        = "${var.environment}-agentgateway-task"
    Environment = var.environment
  }
}

# Application Task Definition (1 vCPU, 2 GB)
resource "aws_ecs_task_definition" "application" {
  family                   = "${var.environment}-application"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024" # 1 vCPU
  memory                   = "2048" # 2 GB
  execution_role_arn       = aws_iam_role.task_execution_role.arn
  task_role_arn            = aws_iam_role.application_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "application"
      image     = var.ecr_repository_urls["application"] != "" ? "${var.ecr_repository_urls["application"]}:${var.image_tag}" : "nginx:latest"
      essential = true

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "SERVICE_NAME"
          value = "application"
        },
        {
          name  = "SERVICE_PORT"
          value = "8000"
        },
        {
          name  = "AWS_REGION"
          value = var.region
        },
        {
          name  = "S3_BUCKET_NAME"
          value = var.s3_bucket_name
        },
        {
          name  = "AGENTGATEWAY_MCP_URL"
          value = "http://agentgateway-service.${var.environment}.local:8081"
        },
        {
          name  = "PROCESSING_TIMEOUT"
          value = "300"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.application.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name        = "${var.environment}-application-task"
    Environment = var.environment
  }
}

# MCP Finance Server Task Definition (0.5 vCPU, 1 GB)
resource "aws_ecs_task_definition" "mcp_finance" {
  family                   = "${var.environment}-mcp-finance"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"  # 0.5 vCPU
  memory                   = "1024" # 1 GB
  execution_role_arn       = aws_iam_role.task_execution_role.arn
  task_role_arn            = aws_iam_role.mcp_finance_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "mcp-finance"
      image     = var.ecr_repository_urls["mcp_finance"] != "" ? "${var.ecr_repository_urls["mcp_finance"]}:${var.image_tag}" : "nginx:latest"
      essential = true

      portMappings = [
        {
          containerPort = 8080
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "SERVICE_NAME"
          value = "mcp-finance-server"
        },
        {
          name  = "SERVICE_PORT"
          value = "8080"
        },
        {
          name  = "SERVER_TYPE"
          value = "finance"
        },
        {
          name  = "AWS_REGION"
          value = var.region
        },
        {
          name  = "S3_BUCKET_NAME"
          value = var.s3_bucket_name
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.mcp_finance.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name        = "${var.environment}-mcp-finance-task"
    Environment = var.environment
  }
}

# MCP HR Server Task Definition (0.5 vCPU, 1 GB)
resource "aws_ecs_task_definition" "mcp_hr" {
  family                   = "${var.environment}-mcp-hr"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"  # 0.5 vCPU
  memory                   = "1024" # 1 GB
  execution_role_arn       = aws_iam_role.task_execution_role.arn
  task_role_arn            = aws_iam_role.mcp_hr_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "mcp-hr"
      image     = var.ecr_repository_urls["mcp_hr"] != "" ? "${var.ecr_repository_urls["mcp_hr"]}:${var.image_tag}" : "nginx:latest"
      essential = true

      portMappings = [
        {
          containerPort = 8080
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "SERVICE_NAME"
          value = "mcp-hr-server"
        },
        {
          name  = "SERVICE_PORT"
          value = "8080"
        },
        {
          name  = "SERVER_TYPE"
          value = "hr"
        },
        {
          name  = "AWS_REGION"
          value = var.region
        },
        {
          name  = "S3_BUCKET_NAME"
          value = var.s3_bucket_name
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.mcp_hr.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name        = "${var.environment}-mcp-hr-task"
    Environment = var.environment
  }
}

# MCP Legal Server Task Definition (0.5 vCPU, 1 GB)
resource "aws_ecs_task_definition" "mcp_legal" {
  family                   = "${var.environment}-mcp-legal"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"  # 0.5 vCPU
  memory                   = "1024" # 1 GB
  execution_role_arn       = aws_iam_role.task_execution_role.arn
  task_role_arn            = aws_iam_role.mcp_legal_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "mcp-legal"
      image     = var.ecr_repository_urls["mcp_legal"] != "" ? "${var.ecr_repository_urls["mcp_legal"]}:${var.image_tag}" : "nginx:latest"
      essential = true

      portMappings = [
        {
          containerPort = 8080
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "SERVICE_NAME"
          value = "mcp-legal-server"
        },
        {
          name  = "SERVICE_PORT"
          value = "8080"
        },
        {
          name  = "SERVER_TYPE"
          value = "legal"
        },
        {
          name  = "AWS_REGION"
          value = var.region
        },
        {
          name  = "S3_BUCKET_NAME"
          value = var.s3_bucket_name
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.mcp_legal.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name        = "${var.environment}-mcp-legal-task"
    Environment = var.environment
  }
}


# ============================================================================
# Service Discovery Services
# ============================================================================

resource "aws_service_discovery_service" "frontend" {
  name = "frontend-service"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }

  tags = {
    Name        = "${var.environment}-frontend-discovery"
    Environment = var.environment
  }
}

resource "aws_service_discovery_service" "agentgateway" {
  name = "agentgateway-service"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }

  tags = {
    Name        = "${var.environment}-agentgateway-discovery"
    Environment = var.environment
  }
}

resource "aws_service_discovery_service" "application" {
  name = "application-service"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }

  tags = {
    Name        = "${var.environment}-application-discovery"
    Environment = var.environment
  }
}

resource "aws_service_discovery_service" "mcp_finance" {
  name = "mcp-finance-service"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }

  tags = {
    Name        = "${var.environment}-mcp-finance-discovery"
    Environment = var.environment
  }
}

resource "aws_service_discovery_service" "mcp_hr" {
  name = "mcp-hr-service"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }

  tags = {
    Name        = "${var.environment}-mcp-hr-discovery"
    Environment = var.environment
  }
}

resource "aws_service_discovery_service" "mcp_legal" {
  name = "mcp-legal-service"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }

  tags = {
    Name        = "${var.environment}-mcp-legal-discovery"
    Environment = var.environment
  }
}

# ============================================================================
# ECS Services
# ============================================================================

# Frontend Service
resource "aws_ecs_service" "frontend" {
  name            = "frontend-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.fargate_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.nlb_target_group_arn
    container_name   = "frontend"
    container_port   = 7860
  }

  service_registries {
    registry_arn = aws_service_discovery_service.frontend.arn
  }

  tags = {
    Name        = "${var.environment}-frontend-service"
    Environment = var.environment
  }

  depends_on = [
    aws_iam_role_policy.frontend_s3_policy,
    aws_iam_role_policy.frontend_efs_policy
  ]
}

# AgentGateway Service
resource "aws_ecs_service" "agentgateway" {
  name            = "agentgateway-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.agentgateway.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.fargate_security_group_id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.agentgateway.arn
  }

  tags = {
    Name        = "${var.environment}-agentgateway-service"
    Environment = var.environment
  }
}

# Application Service
resource "aws_ecs_service" "application" {
  name            = "application-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.application.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.fargate_security_group_id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.application.arn
  }

  tags = {
    Name        = "${var.environment}-application-service"
    Environment = var.environment
  }

  depends_on = [aws_iam_role_policy.application_s3_policy]
}

# MCP Finance Service
resource "aws_ecs_service" "mcp_finance" {
  name            = "mcp-finance-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.mcp_finance.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.fargate_security_group_id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.mcp_finance.arn
  }

  tags = {
    Name        = "${var.environment}-mcp-finance-service"
    Environment = var.environment
  }

  depends_on = [aws_iam_role_policy.mcp_finance_s3_policy]
}

# MCP HR Service
resource "aws_ecs_service" "mcp_hr" {
  name            = "mcp-hr-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.mcp_hr.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.fargate_security_group_id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.mcp_hr.arn
  }

  tags = {
    Name        = "${var.environment}-mcp-hr-service"
    Environment = var.environment
  }

  depends_on = [aws_iam_role_policy.mcp_hr_s3_policy]
}

# MCP Legal Service
resource "aws_ecs_service" "mcp_legal" {
  name            = "mcp-legal-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.mcp_legal.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.fargate_security_group_id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.mcp_legal.arn
  }

  tags = {
    Name        = "${var.environment}-mcp-legal-service"
    Environment = var.environment
  }

  depends_on = [aws_iam_role_policy.mcp_legal_s3_policy]
}


# ============================================================================
# Auto Scaling Configuration
# ============================================================================

# Frontend Auto Scaling Target
resource "aws_appautoscaling_target" "frontend" {
  max_capacity       = 4
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.frontend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Frontend Auto Scaling Policy (CPU-based)
resource "aws_appautoscaling_policy" "frontend_cpu" {
  name               = "${var.environment}-frontend-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.frontend.resource_id
  scalable_dimension = aws_appautoscaling_target.frontend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.frontend.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

# AgentGateway Auto Scaling Target
resource "aws_appautoscaling_target" "agentgateway" {
  max_capacity       = 4
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.agentgateway.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# AgentGateway Auto Scaling Policy (CPU-based)
resource "aws_appautoscaling_policy" "agentgateway_cpu" {
  name               = "${var.environment}-agentgateway-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.agentgateway.resource_id
  scalable_dimension = aws_appautoscaling_target.agentgateway.scalable_dimension
  service_namespace  = aws_appautoscaling_target.agentgateway.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

# Application Auto Scaling Target
resource "aws_appautoscaling_target" "application" {
  max_capacity       = 4
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.application.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Application Auto Scaling Policy (CPU-based)
resource "aws_appautoscaling_policy" "application_cpu" {
  name               = "${var.environment}-application-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.application.resource_id
  scalable_dimension = aws_appautoscaling_target.application.scalable_dimension
  service_namespace  = aws_appautoscaling_target.application.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

# MCP Finance Auto Scaling Target
resource "aws_appautoscaling_target" "mcp_finance" {
  max_capacity       = 4
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.mcp_finance.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# MCP Finance Auto Scaling Policy (CPU-based)
resource "aws_appautoscaling_policy" "mcp_finance_cpu" {
  name               = "${var.environment}-mcp-finance-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.mcp_finance.resource_id
  scalable_dimension = aws_appautoscaling_target.mcp_finance.scalable_dimension
  service_namespace  = aws_appautoscaling_target.mcp_finance.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

# MCP HR Auto Scaling Target
resource "aws_appautoscaling_target" "mcp_hr" {
  max_capacity       = 4
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.mcp_hr.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# MCP HR Auto Scaling Policy (CPU-based)
resource "aws_appautoscaling_policy" "mcp_hr_cpu" {
  name               = "${var.environment}-mcp-hr-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.mcp_hr.resource_id
  scalable_dimension = aws_appautoscaling_target.mcp_hr.scalable_dimension
  service_namespace  = aws_appautoscaling_target.mcp_hr.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

# MCP Legal Auto Scaling Target
resource "aws_appautoscaling_target" "mcp_legal" {
  max_capacity       = 4
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.mcp_legal.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# MCP Legal Auto Scaling Policy (CPU-based)
resource "aws_appautoscaling_policy" "mcp_legal_cpu" {
  name               = "${var.environment}-mcp-legal-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.mcp_legal.resource_id
  scalable_dimension = aws_appautoscaling_target.mcp_legal.scalable_dimension
  service_namespace  = aws_appautoscaling_target.mcp_legal.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}
