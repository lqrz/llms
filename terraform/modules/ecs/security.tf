locals {
  name_frontend_sg = "${var.name_prefix}-front-ecs-tasks-sg"
  name_backend_sg = "${var.name_prefix}-back-ecs-tasks-sg"
}

resource "aws_security_group" "frontend" {
  name        = "${local.name_frontend_sg}"
  description = "Allow frontend ALB to reach frontend tasks"
  vpc_id      = var.vpc_id

  ingress {
    description     = "ALB to Frontend"
    from_port       = var.frontend_port
    to_port         = var.frontend_port
    protocol        = "tcp"
    security_groups = [var.frontend_security_group_id]  # from frontend ALB
  }

  egress {
    description = "all egress (via NAT)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }


  tags = merge(
    {
      Name = "${local.name_frontend_sg}"
    },
    var.tags
  )
}

resource "aws_security_group" "backend" {
  name        = "${local.name_backend_sg}"
  description = "Allow backend ALB to reach backend tasks"
  vpc_id      = var.vpc_id

  ingress {
    description     = "ALB to Backend"
    from_port       = var.backend_port
    to_port         = var.backend_port
    protocol        = "tcp"
    security_groups = [var.backend_security_group_id]  # from backend ALB
  }

  egress {
    description = "all egress (via NAT)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }


  tags = merge(
    {
      Name = "${local.name_backend_sg}"
    },
    var.tags
  )
}
