locals {
  name_cluster = "${var.name_prefix}"

  name_frontend_container = "frontend"
  name_backend_container = "backend"
}

resource "aws_ecs_cluster" "this" {
  name = local.name_cluster

  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }

  tags = merge(
    {
      Name = local.name_cluster
    },
    var.tags
  )
}
