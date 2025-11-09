# Global ALB Module Variables

variable "global_alb_name" {
  description = "Name of the global Application Load Balancer"
  type        = string
}

variable "security_group_ids" {
  description = "List of security group IDs for the global ALB"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs from both zones (must be in different AZs)"
  type        = list(string)
}

variable "zone_a_vpc_id" {
  description = "VPC ID for Zone A (DEV)"
  type        = string
}

variable "zone_b_vpc_id" {
  description = "VPC ID for Zone B (PROD)"
  type        = string
}

variable "zone_a_nlb_ips" {
  description = "List of IP addresses for Zone A NLB (resolved from NLB DNS)"
  type        = list(string)
  default     = []
}

variable "zone_b_nlb_ips" {
  description = "List of IP addresses for Zone B NLB (resolved from NLB DNS)"
  type        = list(string)
  default     = []
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for the global ALB"
  type        = bool
  default     = true
}

variable "health_check_interval" {
  description = "Health check interval in seconds"
  type        = number
  default     = 30
}

variable "health_check_timeout" {
  description = "Health check timeout in seconds"
  type        = number
  default     = 5
}

variable "healthy_threshold" {
  description = "Number of consecutive health checks successes required"
  type        = number
  default     = 2
}

variable "unhealthy_threshold" {
  description = "Number of consecutive health check failures required"
  type        = number
  default     = 3
}

variable "deregistration_delay" {
  description = "Time in seconds before deregistering a target"
  type        = number
  default     = 30
}
