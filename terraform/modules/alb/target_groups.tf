resource "aws_lb_target_group" "frontend" {
  name        = local.name_frontend
  port        = var.frontend_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip" # Fargate

  health_check {
    enabled             = true
    path                = var.frontend_health_path
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = merge(
    {
      Name = local.name_frontend
    },
    var.tags
  )
}

resource "aws_lb_target_group" "backend" {
  name        = local.name_backend
  port        = var.backend_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip" # Fargate

  health_check {
    enabled             = true
    path                = var.backend_health_path
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = merge(
    {
      Name = local.name_backend
    },
    var.tags
  )
}