locals {
  name_log_group = "/ecs/${var.name_prefix}"
  name_tag = "${var.name_prefix}"
}

resource "aws_cloudwatch_log_group" "this" {
  name              = local.name_log_group
  retention_in_days = 7  # permissions issue `logs:PutRetentionPolicy`

  tags = merge(
    {
      Name = "${local.name_tag}"
    },
    var.tags
  )
}
