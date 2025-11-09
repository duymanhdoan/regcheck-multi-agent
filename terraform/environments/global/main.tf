# Global Environment Configuration
# This configuration creates a global ALB that distributes traffic 50/50 between Zone A and Zone B

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Environment = "global"
      ManagedBy   = "Terraform"
      Project     = "InternalFileProcessing"
    }
  }
}

# Data sources to get Zone A and Zone B information
data "terraform_remote_state" "zone_a" {
  backend = "local"

  config = {
    path = "../dev/terraform.tfstate"
  }
}

data "terraform_remote_state" "zone_b" {
  backend = "local"

  config = {
    path = "../prod/terraform.tfstate"
  }
}

# Global ALB Security Group
resource "aws_security_group" "global_alb" {
  name        = "global-alb-sg"
  description = "Security group for global ALB"
  vpc_id      = data.terraform_remote_state.zone_a.outputs.vpc_id

  ingress {
    description = "HTTP from Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from Internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "global-alb-sg"
    Environment = "global"
  }
}

# Global ALB Module
module "global_alb" {
  source = "../../modules/global-alb"

  global_alb_name            = var.global_alb_name
  security_group_ids         = [aws_security_group.global_alb.id]
  public_subnet_ids          = [
    data.terraform_remote_state.zone_a.outputs.public_subnet_id,
    data.terraform_remote_state.zone_b.outputs.public_subnet_id
  ]
  zone_a_vpc_id              = data.terraform_remote_state.zone_a.outputs.vpc_id
  zone_b_vpc_id              = data.terraform_remote_state.zone_b.outputs.vpc_id
  zone_a_alb_arn             = data.terraform_remote_state.zone_a.outputs.alb_arn
  zone_b_alb_arn             = data.terraform_remote_state.zone_b.outputs.alb_arn
  enable_deletion_protection = var.enable_deletion_protection
  health_check_interval      = var.health_check_interval
  healthy_threshold          = var.healthy_threshold
  unhealthy_threshold        = var.unhealthy_threshold
}
