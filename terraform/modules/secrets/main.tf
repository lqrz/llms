resource "aws_secretsmanager_secret" "this" {
  name                    = var.name_prefix
  description             = "Secret for: ${var.name_prefix}"
  recovery_window_in_days = 7

  tags = merge(
    {
      Name = var.name_prefix
    },
    var.tags
  )
}
