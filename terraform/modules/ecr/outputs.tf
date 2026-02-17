output "repository_name" {
  description = "Name of the ECR repository."
  value       = aws_ecr_repository.ecr.name
}

output "repository_arn" {
  description = "ARN of the ECR repository."
  value       = aws_ecr_repository.ecr.arn
}

output "repository_url" {
  description = "URL of the ECR repository."
  value       = aws_ecr_repository.ecr.repository_url
}
