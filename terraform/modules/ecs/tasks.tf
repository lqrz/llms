locals {
  name_frontend_tasks = "${var.name_prefix}-frontend"
  name_frontend_log_prefix = "frontend"

  name_backend_tasks = "${var.name_prefix}-backend"
  name_backend_log_prefix = "backend"

  # --- envvars

  frontend_envvars = concat(
    [ for k, v in var.frontend_envvars  : { name = k, value = v } ],
    [ { name = "API_BASE_URL", value = "http://${var.backend_url}:${var.backend_port}" } ]
  )

  backend_envvars= [ for k, v in var.backend_envvars: { name  = k, value = v } ]

}

resource "aws_ecs_task_definition" "frontend" {
  family                   = local.name_frontend_tasks
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.task_cpu)
  memory                   = tostring(var.task_memory)
  execution_role_arn       = aws_iam_role.this.arn

  container_definitions = jsonencode([
    {
      name      = local.name_frontend_container
      image     = var.frontend_container_image_uri
      essential = true
      portMappings = [
        { containerPort = var.frontend_port, protocol = "tcp" }
      ]
      environment = local.frontend_envvars
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.this.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = local.name_frontend_log_prefix
        }
      }
    }
  ])


  tags = merge(
    {
      Name = local.name_frontend_tasks
    },
    var.tags
  )
}

resource "aws_ecs_task_definition" "backend" {
  family                   = local.name_backend_tasks
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.task_cpu)
  memory                   = tostring(var.task_memory)
  execution_role_arn       = aws_iam_role.this.arn

  container_definitions = jsonencode([
    {
      name      = local.name_backend_container
      image     = var.backend_container_image_uri
      essential = true
      portMappings = [
        { containerPort = var.backend_port, protocol = "tcp" }
      ]
      environment = local.backend_envvars
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.this.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = local.name_backend_log_prefix
        }
      }
      secrets = [
        for s in var.secret_keys: {
          name      = s
          valueFrom = "${var.secrets_manager_arn}:${s}::"
        }
      ]
    }
  ])


  tags = merge(
    {
      Name = local.name_backend_tasks
    },
    var.tags
  )
}