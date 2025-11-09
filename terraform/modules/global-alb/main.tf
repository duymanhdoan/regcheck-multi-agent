# Global Application Load Balancer Module
# This module creates an internet-facing ALB that distributes traffic 50/50 between Zone A (dev) and Zone B (prod)
# Both zones now use Network Load Balancers (NLB) instead of ALBs

# Global Application Load Balancer
resource "aws_lb" "global" {
  name               = var.global_alb_name
  internal           = false
  load_balancer_type = "application"
  security_groups    = var.security_group_ids
  subnets            = var.public_subnet_ids # Must include subnets from both AZs

  enable_deletion_protection       = var.enable_deletion_protection
  enable_http2                     = true
  enable_cross_zone_load_balancing = true

  tags = {
    Name        = var.global_alb_name
    Environment = "global"
    Purpose     = "Multi-Zone Load Balancing"
  }
}

# Target Group for Zone A (DEV) - Points to Zone A NLB
resource "aws_lb_target_group" "zone_a" {
  name        = "global-zone-a-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = var.zone_a_vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = var.healthy_threshold
    unhealthy_threshold = var.unhealthy_threshold
    timeout             = var.health_check_timeout
    interval            = var.health_check_interval
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200,302"
  }

  deregistration_delay = var.deregistration_delay

  tags = {
    Name        = "global-zone-a-tg"
    Environment = "global"
    Zone        = "A"
    Target      = "Zone A NLB"
  }
}

# Target Group for Zone B (PROD) - Points to Zone B NLB
resource "aws_lb_target_group" "zone_b" {
  name        = "global-zone-b-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = var.zone_b_vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = var.healthy_threshold
    unhealthy_threshold = var.unhealthy_threshold
    timeout             = var.health_check_timeout
    interval            = var.health_check_interval
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200,302"
  }

  deregistration_delay = var.deregistration_delay

  tags = {
    Name        = "global-zone-b-tg"
    Environment = "global"
    Zone        = "B"
    Target      = "Zone B NLB"
  }
}

# Register Zone A NLB IPs as targets
# Note: NLB IPs must be resolved and registered manually or via Lambda
# This is a placeholder - actual implementation requires DNS resolution
resource "aws_lb_target_group_attachment" "zone_a_nlb" {
  count            = length(var.zone_a_nlb_ips)
  target_group_arn = aws_lb_target_group.zone_a.arn
  target_id        = var.zone_a_nlb_ips[count.index]
  port             = 80
}

# Register Zone B NLB IPs as targets
# Note: NLB IPs must be resolved and registered manually or via Lambda
# This is a placeholder - actual implementation requires DNS resolution
resource "aws_lb_target_group_attachment" "zone_b_nlb" {
  count            = length(var.zone_b_nlb_ips)
  target_group_arn = aws_lb_target_group.zone_b.arn
  target_id        = var.zone_b_nlb_ips[count.index]
  port             = 80
}

# HTTP Listener with weighted routing (50/50)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.global.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "forward"

    forward {
      target_group {
        arn    = aws_lb_target_group.zone_a.arn
        weight = 50
      }

      target_group {
        arn    = aws_lb_target_group.zone_b.arn
        weight = 50
      }

      stickiness {
        enabled  = true
        duration = 3600 # 1 hour session stickiness
      }
    }
  }

  tags = {
    Name        = "global-http-listener"
    Environment = "global"
  }
}
