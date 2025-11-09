variable "environment" {
  description = "Environment name (dev or prod)"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "vpc_cidr_primary" {
  description = "Primary CIDR block for VPC"
  type        = string
}

variable "vpc_cidr_secondary" {
  description = "Secondary CIDR block for VPC (for application tier)"
  type        = string
}

variable "public_subnet_cidr" {
  description = "CIDR block for public subnet (from primary range)"
  type        = string
}

variable "private_subnet_cidr" {
  description = "CIDR block for private subnet (from secondary range)"
  type        = string
}

variable "availability_zone" {
  description = "Availability zone for subnets"
  type        = string
  default     = "ap-southeast-1a"
}
