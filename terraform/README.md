# Internal File Processing System - Terraform Infrastructure

This directory contains the Terraform infrastructure code for the Internal File Processing System.

## Project Structure

```
terraform/
├── modules/              # Reusable Terraform modules
│   ├── vpc/             # VPC with Primary and Secondary CIDR
│   ├── eks/             # EKS cluster and worker nodes
│   ├── s3/              # S3 bucket with encryption and lifecycle
│   ├── cognito/         # Cognito User Pool
│   └── security-groups/ # Security groups for all layers
├── environments/         # Environment-specific configurations
│   ├── dev/             # Development environment
│   ├── staging/         # Staging environment
│   └── prod/            # Production environment
└── backend/             # Terraform backend setup scripts

## Prerequisites

- Terraform >= 1.5.0
- AWS CLI configured with appropriate credentials
- kubectl for Kubernetes management

## Backend Configuration

The Terraform state is stored in S3 with DynamoDB for state locking.

### Initial Backend Setup

Before deploying any infrastructure, you must create the backend resources:

```bash
cd backend
terraform init
terraform apply
```

This will create:
- S3 bucket for Terraform state
- DynamoDB table for state locking
- KMS key for state encryption

## Deployment

### 1. Initialize Backend

```bash
cd environments/dev
terraform init
```

### 2. Plan Infrastructure

```bash
terraform plan -out=tfplan
```

### 3. Apply Infrastructure

```bash
terraform apply tfplan
```

### 4. Destroy Infrastructure (if needed)

```bash
terraform destroy
```

## Environment Variables

Each environment requires the following variables to be set in `terraform.tfvars`:

- `region`: AWS region (default: ap-southeast-1)
- `environment`: Environment name (dev/staging/prod)
- `vpc_primary_cidr`: Primary CIDR block (default: 10.0.0.0/16)
- `vpc_secondary_cidr`: Secondary CIDR block (default: 100.64.0.0/16)
- `availability_zones`: List of AZs (default: ["ap-southeast-1a"])

## Module Documentation

See individual module README files for detailed documentation:
- [VPC Module](modules/vpc/README.md)
- [EKS Module](modules/eks/README.md)
- [S3 Module](modules/s3/README.md)
- [Cognito Module](modules/cognito/README.md)
- [Security Groups Module](modules/security-groups/README.md)
