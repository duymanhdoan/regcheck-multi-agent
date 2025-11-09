# Global Environment Outputs

output "global_alb_dns_name" {
  description = "DNS name of the global ALB (use this for accessing the application)"
  value       = module.global_alb.global_alb_dns_name
}

output "global_alb_arn" {
  description = "ARN of the global ALB"
  value       = module.global_alb.global_alb_arn
}

output "global_alb_zone_id" {
  description = "Zone ID of the global ALB (for Route53 alias records)"
  value       = module.global_alb.global_alb_zone_id
}

output "zone_a_target_group_arn" {
  description = "ARN of Zone A target group"
  value       = module.global_alb.zone_a_target_group_arn
}

output "zone_b_target_group_arn" {
  description = "ARN of Zone B target group"
  value       = module.global_alb.zone_b_target_group_arn
}
