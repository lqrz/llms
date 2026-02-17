output "cluster_name" {
  description = "Name of the ECS cluster."
  value       = aws_ecs_cluster.this.name
}

output "cluster_arn" {
  description = "ARN of the ECS cluster."
  value       = aws_ecs_cluster.this.arn
}

output "frontend_task_security_group_id" {
  description = "Frontend task SG."
  value = aws_security_group.frontend.id
}

output "backend_task_security_group_id" {
  description = "Backend task SG."
  value = aws_security_group.backend.id
}
