locals {
  name_frontend_service = "${var.name_prefix}-frontend"
  name_backend_service = "${var.name_prefix}-backend"
}

resource "aws_ecs_service" "frontend" {
  name            = local.name_frontend_service
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.frontend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.frontend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.frontend_alb_target_group_arn
    container_name   = local.name_frontend_container
    container_port   = var.frontend_port
  }

  tags = merge(
    {
      Name = local.name_frontend_service
    },
    var.tags
  )
}

resource "aws_ecs_service" "backend" {
  name            = local.name_backend_service
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.backend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.backend_alb_target_group_arn
    container_name   = local.name_backend_container
    container_port   = var.backend_port
  }

  tags = merge(
    {
      Name = local.name_backend_service
    },
    var.tags
  )
}
