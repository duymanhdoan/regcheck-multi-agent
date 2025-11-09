# Cognito Module Variables

variable "user_pool_name" {
  description = "Name of the Cognito User Pool"
  type        = string
}

variable "environment" {
  description = "Environment name (dev or prod)"
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be either 'dev' or 'prod'."
  }
}

variable "create_domain" {
  description = "Whether to create a Cognito User Pool domain"
  type        = bool
  default     = false
}

variable "domain_prefix" {
  description = "Domain prefix for Cognito hosted UI"
  type        = string
  default     = "internal-users"
}
