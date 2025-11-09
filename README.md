# AWS Multi-AZ Infrastructure - Internal File Processing System

Enterprise-grade AWS infrastructure for processing files with MCP (Model Context Protocol) data enrichment, deployed across multiple availability zones for high availability.

## Overview

This system provides a highly available, scalable architecture for processing files with department-specific data enrichment using MCP servers. Built on Amazon EKS (Kubernetes) with multi-AZ deployment for production-grade reliability.

### Key Features

- **High Availability**: Multi-AZ deployment across 3 availability zones
- **Kubernetes-based**: Amazon EKS for container orchestration
- **Multi-Department Support**: Finance, HR, and Legal MCP servers
- **Auto-Scaling**: Horizontal Pod Autoscaler (HPA) for dynamic scaling
- **Secure by Design**: Private subnets, VPC endpoints, JWT auth, encryption at rest
- **Dual Access**: External users (Internet) and On-Premise users (VPN/Direct Connect)
- **Infrastructure as Code**: Fully automated with Terraform

## Architecture

### High-Level Overview

The system is deployed across multiple availability zones in AWS Region ap-southeast-1 (Singapore) for high availability and fault tolerance.

```
┌─────────────────────────────────────────────────────────────┐
│                    External Users (Internet)                │
│                    On-Premise Users (VPN/DX)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Internet Gateway / VPN Gateway                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Application Load Balancer (Internet + Internal)      │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   AZ-1a      │  │   AZ-1b      │  │   AZ-1c      │
│   (MVP)      │  │              │  │              │
├──────────────┤  ├──────────────┤  ├──────────────┤
│ Public       │  │ Public       │  │ Public       │
│ Subnet       │  │ Subnet       │  │ Subnet       │
│ NAT Gateway  │  │ NAT Gateway  │  │ NAT Gateway  │
├──────────────┤  ├──────────────┤  ├──────────────┤
│ Private      │  │ Private      │  │ Private      │
│ Subnet       │  │ Subnet       │  │ Subnet       │
│              │  │              │  │              │
│ EKS Workers  │  │ EKS Workers  │  │ EKS Workers  │
│ - Frontend   │  │ - Frontend   │  │ - Frontend   │
│ - Gateway    │  │ - Gateway    │  │ - Gateway    │
│ - App        │  │ - App        │  │ - App        │
│ - MCP        │  │ - MCP        │  │ - MCP        │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   AWS Managed Services                       │
│  - S3 (File Storage)                                        │
│  - Cognito (Authentication)                                 │
│  - CloudWatch (Monitoring)                                  │
│  - ECR (Container Registry)                                 │
└─────────────────────────────────────────────────────────────┘
```

### Architecture Diagrams

Detailed architecture diagrams are available in the `generated-diagrams/` directory:

- **Multi-AZ Infrastructure**: Complete infrastructure overview with all 3 availability zones
- **Network Topology**: VPC design with Primary (10.0.0.0/16) and Secondary CIDR (100.64.0.0/16)
- **Traffic Flows**: External and on-premise user access patterns
- **EKS Deployment**: Kubernetes cluster architecture across multiple AZs

**Note**: Architecture diagrams are generated and stored in `generated-diagrams/` (gitignored). To regenerate:

```bash
python src-gen-images/generate_diagram_v3.py
```

### Network Design

**VPC CIDR Blocks:**
- Primary CIDR: `10.0.0.0/16` (Public subnets for ALB)
- Secondary CIDR: `100.64.0.0/16` (Private subnets for EKS pods)

**Subnets per AZ:**
- Public Subnet: `10.0.x.0/24` (251 IPs) - ALB, NAT Gateway
- Private Subnet: `100.64.x.0/20` (4,091 IPs) - EKS worker nodes and pods

**Why Secondary CIDR?**
- Provides 4,091 IPs per AZ for pod scaling
- Follows AWS best practice for EKS custom networking
- Prevents IP exhaustion as pods scale

## Services

### Frontend (Langflow)
- User interface for file upload and processing
- Built on Langflow framework
- Cognito authentication

### AgentGateway
- Dual-mode gateway (API + MCP)
- Routes requests to appropriate services
- JWT token validation
- Department-based access control

### Application
- File processing orchestration
- Downloads files from S3
- Calls MCP servers for data enrichment
- Uploads processed results

### MCP Servers (Finance, HR, Legal)
- Department-specific data and tools
- MCP JSON-RPC protocol
- S3-based data retrieval

## Quick Start

```bash
# 1. Set environment variables
export AWS_ACCOUNT_ID=123456789012
export AWS_REGION=ap-southeast-1
export ENVIRONMENT=dev

# 2. Deploy infrastructure
cd terraform/environments/dev
terraform init
terraform apply -var-file=terraform.tfvars

# 3. Build and push images
cd ../../..
./build-all.sh

# 4. Deploy services
for service in frontend agentgateway application mcp-finance mcp-hr mcp-legal; do
  aws ecs update-service \
    --cluster dev-ecs-cluster \
    --service ${service}-service \
    --force-new-deployment
done

# 5. Get application URL
cd terraform/environments/dev
terraform output alb_dns_name
```

See [QUICK-START.md](QUICK-START.md) for more details.

## Documentation

- [Quick Start Guide](QUICK-START.md) - Fast deployment
- [Deployment Guide](DEPLOYMENT.md) - Detailed deployment instructions
- [Frontend README](frontend/README.md) - Frontend service details
- [AgentGateway README](agentgateway/README.md) - Gateway service details
- [Application README](application/README.md) - Processing service details
- [MCP Servers README](mcp-servers/README.md) - MCP servers details

## Project Structure

```
.
├── terraform/                     # Infrastructure as Code
│   ├── modules/                  # Reusable Terraform modules
│   │   ├── vpc/                 # VPC with Primary & Secondary CIDR
│   │   ├── eks/                 # EKS cluster (Multi-AZ)
│   │   ├── alb/                 # Application Load Balancer
│   │   ├── ecr/                 # Container registries
│   │   ├── s3/                  # S3 buckets
│   │   └── cognito/             # User authentication
│   └── environments/             # Environment-specific configs
│       ├── dev/                 # Development (Single AZ)
│       └── prod/                # Production (Multi-AZ)
├── kubernetes/                   # Kubernetes manifests
│   ├── frontend/                # Frontend deployment
│   ├── agentgateway/            # AgentGateway deployment
│   ├── application/             # Application deployment
│   └── mcp-servers/             # MCP servers deployment
├── src-gen-images/              # Generated diagram scripts (gitignored)
├── generated-diagrams/          # Architecture diagrams (gitignored)
├── docs/                        # Documentation (gitignored)
│   ├── interal-docs/           # Internal architecture docs
│   └── exteral-docs/           # External documentation
├── frontend/                    # Frontend service
├── agentgateway/                # AgentGateway service
├── application/                 # Application service
├── mcp-servers/                 # MCP server services
│   ├── src/base/               # Base MCP implementation
│   ├── src/finance/            # Finance MCP server
│   ├── src/hr/                 # HR MCP server
│   └── src/legal/              # Legal MCP server
├── build-all.sh                 # Build all services
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## Technology Stack

- **Infrastructure**: Amazon EKS, VPC (Primary + Secondary CIDR), ALB, S3, Cognito
- **Container Orchestration**: Kubernetes (Amazon EKS)
- **Container Registry**: Amazon ECR
- **Networking**: Multi-AZ deployment, VPN Gateway, Direct Connect
- **Backend**: Python 3.11, FastAPI
- **Frontend**: Langflow (Python-based)
- **IaC**: Terraform (modular design)
- **Protocol**: MCP (Model Context Protocol)
- **Monitoring**: CloudWatch Container Insights

## Requirements

- AWS CLI configured
- Docker installed
- Terraform >= 1.0
- Python 3.11+ (for local development)
- AWS account with appropriate permissions

## Development

### Local Development

Each service can be run locally:

```bash
# Frontend
cd frontend
# Follow frontend/README.md

# AgentGateway
cd agentgateway
pip install -r requirements.txt
uvicorn src.main:app --reload

# Application
cd application
pip install -r requirements.txt
uvicorn src.main:app --reload

# MCP Servers
cd mcp-servers
export SERVER_TYPE=finance
pip install -r requirements.txt
uvicorn src.finance.main:app --reload
```

### Building Images

```bash
# Build all services
./build-all.sh

# Build individual service
cd <service-directory>
./build.sh
```

## Deployment

### Development Environment

```bash
export ENVIRONMENT=dev
cd terraform/environments/dev
terraform apply -var-file=terraform.tfvars
```

### Production Environment

```bash
export ENVIRONMENT=prod
cd terraform/environments/prod
terraform apply -var-file=terraform.tfvars
```

## Monitoring

### CloudWatch Logs

```bash
# View service logs
aws logs tail /ecs/dev/frontend --follow
aws logs tail /ecs/dev/agentgateway --follow
aws logs tail /ecs/dev/application --follow
```

### CloudWatch Metrics

- ECS Service metrics (CPU, Memory, Task count)
- ALB metrics (Request count, Response time)
- Custom application metrics

## Cost Estimation

### MVP Environment - Single AZ (~$301/month)
- EKS Control Plane: $73
- EC2 (2x t3.large): $120
- NAT Gateway: $45
- ALB: $23
- S3 (100 GB): $3
- Cognito (1000 users): $5
- CloudWatch: $10
- VPC Endpoints: $22

### Enterprise Environment - Multi-AZ (~$2,470/month)
- EKS Control Plane: $73
- EC2 (6x m5.2xlarge): $1,800
- NAT Gateway (3x): $135
- ALB: $23
- S3 (1 TB): $23
- Cognito (10K users): $50
- CloudWatch: $50
- VPC Endpoints: $66
- Direct Connect (1Gbps): $250

**Cost Multiplier**: 8.2x (MVP → Enterprise)

## Security

### Network Security
- All EKS worker nodes in private subnets (Secondary CIDR: 100.64.0.0/16)
- ALB in public subnet as single entry point
- Security groups with least privilege
- VPC endpoints for private AWS service access
- Network ACLs for additional layer of security

### Authentication & Authorization
- Cognito user authentication for external users
- IAM authentication for on-premise users
- JWT token validation
- IAM Roles for Service Accounts (IRSA)
- Kubernetes RBAC

### Data Protection
- S3 encryption at rest (SSE-S3)
- EBS volumes encrypted with AWS managed keys
- EKS secrets encrypted with KMS
- TLS 1.3 for data in transit
- VPN/Direct Connect encryption for on-premise connectivity

## Scaling

### Horizontal Pod Autoscaler (HPA)

```bash
# Scale based on CPU utilization
kubectl autoscale deployment frontend \
  --cpu-percent=70 \
  --min=1 \
  --max=4
```

### Cluster Autoscaler

Automatically scales EKS worker nodes based on pod requirements:
- Min nodes: 1 per AZ
- Max nodes: 10 per AZ
- Supports multiple instance types

### Manual Scaling

```bash
# Scale deployment
kubectl scale deployment frontend --replicas=3

# Scale across availability zones
kubectl get pods -o wide  # Check pod distribution
```

### Configuration

Configure in Kubernetes manifests:
```yaml
spec:
  replicas: 1
  # HPA will manage replicas between 1-4
```

## Troubleshooting

See [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting) for detailed troubleshooting guide.

Common issues:
- Services not starting → Check CloudWatch logs
- Images not pulling → Verify ECR permissions
- ALB health checks failing → Check security groups
- MCP servers not responding → Verify S3 data exists

## Generated Files & Gitignore

The following directories are gitignored and contain generated content:

- **`src-gen-images/`**: Python scripts for generating architecture diagrams
- **`generated-diagrams/`**: Generated PNG and Draw.io architecture diagrams
- **`docs/`**: Internal and external documentation
- **`test-reports/`**: Test execution reports
- **`.pytest_cache/`**: Python test cache
- **`.kiro/`**: Kiro IDE configuration
- **`.vscode/`**: VS Code configuration

To regenerate architecture diagrams:

```bash
# Install dependencies
pip install diagrams

# Generate diagrams
python src-gen-images/generate_diagram_v3.py
python src-gen-images/generate_diagram_template_based.py

# Output will be in generated-diagrams/
ls -lh generated-diagrams/
```

## Contributing

1. Create feature branch
2. Make changes
3. Test locally
4. Build and test Docker images
5. Update documentation if needed
6. Regenerate diagrams if architecture changes
7. Submit pull request

## License

Internal use only.

## Support

For issues or questions:
1. Check documentation
2. Review CloudWatch logs
3. Verify Terraform state
4. Contact DevOps team
