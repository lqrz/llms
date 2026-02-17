output "secrets_manager_arn" {
    description = "Secret manager ARN."
    value = aws_secretsmanager_secret.this.arn
}
