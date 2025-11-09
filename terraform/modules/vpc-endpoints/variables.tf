variable "environment" {
  description = "Environment name (dev or prod)"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "private_subnet_id" {
  description = "ID of the private subnet for interface endpoints"
  type        = string
}

variable "private_route_table_id" {
  description = "ID of the private route table for gateway endpoints"
  type        = string
}

variable "fargate_security_group_id" {
  description = "ID of the Fargate tasks security group"
  type        = string
}
