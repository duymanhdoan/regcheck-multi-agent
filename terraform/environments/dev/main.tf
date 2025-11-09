# Dev Environment Main Configuration

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
      Environment = var.environment
      ManagedBy   = "Terraform"
      Project     = "InternalFileProcessing"
    }
  }
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"

  environment          = var.environment
  region               = var.region
  vpc_cidr_primary     = var.vpc_cidr_primary
  vpc_cidr_secondary   = var.vpc_cidr_secondary
  public_subnet_cidr   = var.public_subnet_cidr
  private_subnet_cidr  = var.private_subnet_cidr
  availability_zone    = var.availability_zone
}

# VPC Endpoints Module
module "vpc_endpoints" {
  source = "../../modules/vpc-endpoints"

  environment              = var.environment
  vpc_id                   = module.vpc.vpc_id
  private_subnet_id        = module.vpc.private_subnet_id
  private_route_table_id   = module.vpc.private_route_table_id
  fargate_security_group_id = module.security_groups.fargate_tasks_security_group_id
  region                   = var.region
}

# Security Groups Module
module "security_groups" {
  source = "../../modules/security-groups"

  environment = var.environment
  vpc_id      = module.vpc.vpc_id
}

# S3 Module
module "s3" {
  source = "../../modules/s3"

  bucket_name = var.s3_bucket_name
  environment = var.environment
}

# Cognito Module
module "cognito" {
  source = "../../modules/cognito"

  user_pool_name = var.cognito_user_pool_name
  environment    = var.environment
  create_domain  = var.cognito_create_domain
  domain_prefix  = var.cognito_domain_prefix
}

# NLB Module (Network Load Balancer for single-AZ)
module "nlb" {
  source = "../../modules/nlb"

  environment                = var.environment
  nlb_name                   = var.nlb_name
  vpc_id                     = module.vpc.vpc_id
  public_subnet_ids          = [module.vpc.public_subnet_id]
  enable_deletion_protection = var.nlb_enable_deletion_protection
  health_check_path          = var.nlb_health_check_path
  health_check_interval      = var.nlb_health_check_interval
  healthy_threshold          = var.nlb_healthy_threshold
  unhealthy_threshold        = var.nlb_unhealthy_threshold
}

# EFS Module
module "efs" {
  source = "../../modules/efs"

  environment           = var.environment
  private_subnet_ids    = [module.vpc.private_subnet_id]
  efs_security_group_id = module.security_groups.efs_security_group_id
}

# ECS Fargate Module
module "ecs_fargate" {
  source = "../../modules/ecs-fargate"

  environment               = var.environment
  region                    = var.region
  vpc_id                    = module.vpc.vpc_id
  private_subnet_ids        = [module.vpc.private_subnet_id]
  fargate_security_group_id = module.security_groups.fargate_tasks_security_group_id
  nlb_target_group_arn      = module.nlb.frontend_target_group_arn
  s3_bucket_name            = module.s3.bucket_name
  s3_bucket_arn             = module.s3.bucket_arn
  cognito_user_pool_id      = module.cognito.user_pool_id
  efs_file_system_id        = module.efs.efs_file_system_id
  efs_file_system_arn       = module.efs.efs_file_system_arn
  efs_access_point_id       = module.efs.efs_access_point_id
  efs_access_point_arn      = module.efs.efs_access_point_arn
  ecr_repository_urls       = var.ecr_repository_urls
  image_tag                 = var.image_tag
}
