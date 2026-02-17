output "frontend_security_group_id" {
  description = "Frontend ALB security group ID."
  value       = aws_security_group.frontend.id
}

output "frontend_target_group_arn" {
  description = "Frontend ALB target group ARN."
  value  = aws_lb_target_group.frontend.arn
}

output "backend_security_group_id" {
  description = "Backend ALB security group ID."
  value       = aws_security_group.backend.id
}

output "backend_target_group_arn" {
  description = "Backend ALB target group ARN."
  value  = aws_lb_target_group.backend.arn
}

output "backend_dns" {
  description = "Backend ALB DNS."
  value = aws_lb.backend.dns_name
}
