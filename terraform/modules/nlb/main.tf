# Network Load Balancer Module (Single-AZ)

resource "aws_lb" "main" {
  name               = var.nlb_name
  internal           = false
  load_balancer_type = "network"
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.enable_deletion_protection
  enable_cross_zone_load_balancing = true

  tags = {
    Name        = var.nlb_name
    Environment = var.environment
  }
}

# Target Group for Frontend (HTTP on port 80)
resource "aws_lb_target_group" "frontend" {
  name        = "${var.environment}-frontend-tg"
  port        = 80
  protocol    = "TCP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    protocol            = "HTTP"
    path                = var.health_check_path
    interval            = var.health_check_interval
    healthy_threshold   = var.healthy_threshold
    unhealthy_threshold = var.unhealthy_threshold
  }

  deregistration_delay = 30

  tags = {
    Name        = "${var.environment}-frontend-tg"
    Environment = var.environment
  }
}

# Listener for Frontend (Port 80)
resource "aws_lb_listener" "frontend" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }

  tags = {
    Name        = "${var.environment}-frontend-listener"
    Environment = var.environment
  }
}
