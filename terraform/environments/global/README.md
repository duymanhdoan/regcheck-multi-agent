# Global Environment - 50/50 Traffic Distribution

This environment creates a Global Application Load Balancer that distributes traffic 50/50 between Zone A (DEV) and Zone B (PROD).

## Prerequisites

Before deploying the global environment, you must:

1. Deploy Zone A (DEV) environment
2. Deploy Zone B (PROD) environment
3. Ensure both zones are healthy and operational

## Deployment

```bash
# Initialize Terraform
terraform init

# Plan the deployment
terraform plan -var-file=terraform.tfvars

# Apply the configuration
terraform apply -var-file=terraform.tfvars

# Get the Global ALB DNS name
terraform output global_alb_dns_name
```

## Configuration

The global environment uses remote state to reference Zone A and Zone B outputs:

```hcl
data "terraform_remote_state" "zone_a" {
  backend = "local"
  config = {
    path = "../dev/terraform.tfstate"
  }
}

data "terraform_remote_state" "zone_b" {
  backend = "local"
  config = {
    path = "../prod/terraform.tfstate"
  }
}
```

## Outputs

After deployment, you can access the following outputs:

```bash
# Get Global ALB DNS name (use this for accessing the application)
terraform output global_alb_dns_name

# Get Global ALB ARN
terraform output global_alb_arn

# Get Zone A target group ARN
terraform output zone_a_target_group_arn

# Get Zone B target group ARN
terraform output zone_b_target_group_arn
```

## Traffic Distribution

The Global ALB distributes traffic as follows:

- **50%** to Zone A (DEV) - ap-southeast-1a
- **50%** to Zone B (PROD) - ap-southeast-1b

Session stickiness ensures users stay in the same zone for 1 hour.

## Accessing the Application

Use the Global ALB DNS name to access the application:

```bash
# Get the DNS name
GLOBAL_ALB_DNS=$(terraform output -raw global_alb_dns_name)

# Access the application
curl http://$GLOBAL_ALB_DNS/health

# Or open in browser
echo "http://$GLOBAL_ALB_DNS"
```

## Monitoring

You can monitor the Global ALB using CloudWatch metrics:

- RequestCount
- TargetResponseTime
- HTTPCode_Target_2XX_Count
- HTTPCode_Target_4XX_Count
- HTTPCode_Target_5XX_Count
- HealthyHostCount
- UnHealthyHostCount

## Failover

If one zone becomes unhealthy:

1. The Global ALB will detect the unhealthy zone through health checks
2. All traffic will be automatically routed to the healthy zone
3. Once the unhealthy zone recovers, traffic will resume 50/50 distribution

## Cleanup

To destroy the global environment:

```bash
terraform destroy -var-file=terraform.tfvars
```

**Note**: You should destroy the global environment before destroying Zone A or Zone B.

## Troubleshooting

### Global ALB not distributing traffic evenly

Check the target group health:

```bash
aws elbv2 describe-target-health \
  --target-group-arn $(terraform output -raw zone_a_target_group_arn)

aws elbv2 describe-target-health \
  --target-group-arn $(terraform output -raw zone_b_target_group_arn)
```

### One zone receiving all traffic

This is expected if one zone is unhealthy. Check the health of both zone ALBs:

```bash
# Check Zone A ALB
aws elbv2 describe-load-balancers \
  --names dev-alb-ap-southeast-1

# Check Zone B ALB
aws elbv2 describe-load-balancers \
  --names prod-alb-ap-southeast-1
```

### Session stickiness not working

Verify that session stickiness is enabled:

```bash
aws elbv2 describe-listeners \
  --load-balancer-arn $(terraform output -raw global_alb_arn)
```

## Cost

The Global ALB adds the following costs:

- ALB: ~$20/month
- Data transfer: Variable based on usage

Total additional cost: ~$20-30/month
