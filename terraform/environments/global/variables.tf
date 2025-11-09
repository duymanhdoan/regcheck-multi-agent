# Global Environment Variables

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "global_alb_name" {
  description = "Name of the global Application Load Balancer"
  type        = string
  default     = "global-alb-ap-southeast-1"
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
