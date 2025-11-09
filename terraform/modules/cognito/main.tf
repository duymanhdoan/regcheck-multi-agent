# Cognito Module
# Creates Cognito User Pool with password policy and JWT token configuration

resource "aws_cognito_user_pool" "main" {
  name = var.user_pool_name

  # Password policy configuration
  password_policy {
    minimum_length                   = 12
    require_uppercase                = true
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = false
    temporary_password_validity_days = 7
  }

  # Account recovery settings
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # Auto-verified attributes
  auto_verified_attributes = ["email"]

  # User attribute schema
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  schema {
    name                = "department"
    attribute_data_type = "String"
    required            = false
    mutable             = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  # MFA configuration - OFF for dev environment simplicity
  mfa_configuration = "OFF"

  tags = {
    Name        = var.user_pool_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# User Pool Client
resource "aws_cognito_user_pool_client" "main" {
  name         = "${var.user_pool_name}-client"
  user_pool_id = aws_cognito_user_pool.main.id

  # JWT token expiration settings
  access_token_validity  = 1  # 1 hour
  id_token_validity      = 1  # 1 hour
  refresh_token_validity = 30 # 30 days

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  # Authentication flows
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]

  # Prevent user existence errors
  prevent_user_existence_errors = "ENABLED"

  # Read and write attributes
  read_attributes = [
    "email",
    "email_verified",
    "custom:department"
  ]

  write_attributes = [
    "email",
    "custom:department"
  ]
}

# User Pool Domain (optional, for hosted UI)
resource "aws_cognito_user_pool_domain" "main" {
  count        = var.create_domain ? 1 : 0
  domain       = "${var.environment}-${var.domain_prefix}"
  user_pool_id = aws_cognito_user_pool.main.id
}
