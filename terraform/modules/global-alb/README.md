# Global ALB Module

This module creates a Global Application Load Balancer that distributes traffic 50/50 between Zone A (DEV) and Zone B (PROD).

## Features

- Internet-facing Application Load Balancer
- Weighted routing: 50% to Zone A, 50% to Zone B
- Session stickiness (1 hour) - ensures users stay in the same zone during their session
- Multi-AZ deployment (ap-southeast-1a + ap-southeast-1b)
- Health checks on both zone ALBs
- Automatic failover if one zone becomes unhealthy
- Cross-zone load balancing enabled

## Architecture

```
Internet Users
      ↓
Global ALB (global-alb-ap-southeast-1)
      ↓
   ┌──┴──┐
   │     │
  50%   50%
   │     │
   ↓     ↓
Zone A  Zone B
(DEV)   (PROD)
AZ-1a   AZ-1b
```

## Usage

```hcl
module "global_alb" {
  source = "../../modules/global-alb"

  global_alb_name    = "global-alb-ap-southeast-1"
  security_group_ids = [aws_security_group.global_alb.id]
  
  # Public subnets from both zones (different AZs)
  public_subnet_ids = [
    data.terraform_remote_state.zone_a.outputs.public_subnet_id,  # ap-southeast-1a
    data.terraform_remote_state.zone_b.outputs.public_subnet_id   # ap-southeast-1b
  ]
  
  zone_a_vpc_id  = data.terraform_remote_state.zone_a.outputs.vpc_id
  zone_b_vpc_id  = data.terraform_remote_state.zone_b.outputs.vpc_id
  zone_a_alb_arn = data.terraform_remote_state.zone_a.outputs.alb_arn
  zone_b_alb_arn = data.terraform_remote_state.zone_b.outputs.alb_arn
  
  enable_deletion_protection = true
  health_check_interval      = 30
  healthy_threshold          = 2
  unhealthy_threshold        = 3
}
```

## Requirements

- Zone A (DEV) must be deployed first
- Zone B (PROD) must be deployed second
- Both zones must be in the same region but different availability zones
- Zone A must be in ap-southeast-1a
- Zone B must be in ap-southeast-1b

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| global_alb_name | Name of the global ALB | `string` | n/a | yes |
| security_group_ids | List of security group IDs | `list(string)` | n/a | yes |
| public_subnet_ids | List of public subnet IDs from both zones | `list(string)` | n/a | yes |
| zone_a_vpc_id | VPC ID for Zone A | `string` | n/a | yes |
| zone_b_vpc_id | VPC ID for Zone B | `string` | n/a | yes |
| zone_a_alb_arn | ARN of Zone A ALB | `string` | n/a | yes |
| zone_b_alb_arn | ARN of Zone B ALB | `string` | n/a | yes |
| enable_deletion_protection | Enable deletion protection | `bool` | `true` | no |
| health_check_interval | Health check interval in seconds | `number` | `30` | no |
| healthy_threshold | Healthy threshold | `number` | `2` | no |
| unhealthy_threshold | Unhealthy threshold | `number` | `3` | no |

## Outputs

| Name | Description |
|------|-------------|
| global_alb_id | ID of the global ALB |
| global_alb_arn | ARN of the global ALB |
| global_alb_dns_name | DNS name of the global ALB (use this for accessing the application) |
| global_alb_zone_id | Zone ID of the global ALB (for Route53 alias records) |
| zone_a_target_group_arn | ARN of Zone A target group |
| zone_b_target_group_arn | ARN of Zone B target group |

## Deployment Order

1. Deploy Zone A (DEV):
   ```bash
   cd terraform/environments/dev
   terraform apply
   ```

2. Deploy Zone B (PROD):
   ```bash
   cd terraform/environments/prod
   terraform apply
   ```

3. Deploy Global ALB:
   ```bash
   cd terraform/environments/global
   terraform apply
   ```

4. Get Global ALB DNS name:
   ```bash
   terraform output global_alb_dns_name
   ```

## Traffic Distribution

The Global ALB uses weighted target groups to distribute traffic:

- **Zone A Target Group**: Weight 50
- **Zone B Target Group**: Weight 50

Session stickiness is enabled with a duration of 1 hour (3600 seconds), ensuring that once a user is routed to a zone, they will continue to be routed to the same zone for the duration of their session.

## Health Checks

The Global ALB performs health checks on both zone ALBs:

- **Path**: `/health`
- **Protocol**: HTTP
- **Interval**: 30 seconds
- **Timeout**: 5 seconds
- **Healthy threshold**: 2 consecutive successes
- **Unhealthy threshold**: 3 consecutive failures

If one zone becomes unhealthy, all traffic will be automatically routed to the healthy zone.

## Security

The Global ALB requires a security group that allows:

- **Inbound**: HTTP (80) and HTTPS (443) from 0.0.0.0/0
- **Outbound**: All traffic to 0.0.0.0/0

Example security group:

```hcl
resource "aws_security_group" "global_alb" {
  name        = "global-alb-sg"
  description = "Security group for global ALB"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP from Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from Internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

## Notes

- The Global ALB must be deployed in a VPC that has subnets in both availability zones (ap-southeast-1a and ap-southeast-1b)
- The target type for the target groups is `alb`, which means the targets are the zone ALBs themselves
- Cross-zone load balancing is enabled by default
- HTTP/2 is enabled by default
