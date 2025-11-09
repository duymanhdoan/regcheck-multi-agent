# Global ALB Module Outputs

output "global_alb_id" {
  description = "ID of the global ALB"
  value       = aws_lb.global.id
}

output "global_alb_arn" {
  description = "ARN of the global ALB"
  value       = aws_lb.global.arn
}

output "global_alb_dns_name" {
  description = "DNS name of the global ALB"
  value       = aws_lb.global.dns_name
}

output "global_alb_zone_id" {
  description = "Zone ID of the global ALB"
  value       = aws_lb.global.zone_id
}

output "zone_a_target_group_arn" {
  description = "ARN of Zone A target group"
  value       = aws_lb_target_group.zone_a.arn
}

output "zone_b_target_group_arn" {
  description = "ARN of Zone B target group"
  value       = aws_lb_target_group.zone_b.arn
}

output "http_listener_arn" {
  description = "ARN of the HTTP listener"
  value       = aws_lb_listener.http.arn
}
