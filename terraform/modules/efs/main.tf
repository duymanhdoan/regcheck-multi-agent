# EFS File System Module
# This module creates an EFS file system for persistent storage

# EFS File System
resource "aws_efs_file_system" "langflow" {
  creation_token = "${var.environment}-langflow-efs"
  encrypted      = true

  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"

  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }

  tags = {
    Name        = "${var.environment}-langflow-efs"
    Environment = var.environment
    Purpose     = "Langflow persistent storage"
  }
}

# EFS Mount Targets (one per private subnet)
resource "aws_efs_mount_target" "langflow" {
  count = length(var.private_subnet_ids)

  file_system_id  = aws_efs_file_system.langflow.id
  subnet_id       = var.private_subnet_ids[count.index]
  security_groups = [var.efs_security_group_id]
}

# EFS Access Point for Langflow
resource "aws_efs_access_point" "langflow" {
  file_system_id = aws_efs_file_system.langflow.id

  posix_user {
    gid = 1000
    uid = 1000
  }

  root_directory {
    path = "/langflow"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "755"
    }
  }

  tags = {
    Name        = "${var.environment}-langflow-access-point"
    Environment = var.environment
  }
}
