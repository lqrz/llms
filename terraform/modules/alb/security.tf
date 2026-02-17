locals {
  name_frontend_sg = "${var.name_prefix}-front-alb-sg" 
  name_backend_sg = "${var.name_prefix}-back-alb-sg" 
}

resource "aws_security_group" "frontend" {
  name        = local.name_frontend_sg
  description = "Security group for the frontend ALB."
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    {
      Name = local.name_frontend_sg
    },
    var.tags
  )
}

resource "aws_security_group" "backend" {
  name        = local.name_backend_sg
  description = "Security group for backend ALB."
  vpc_id      = var.vpc_id

  ingress {
    security_groups= [var.frontend_task_security_group_id]
    from_port   = var.backend_port
    to_port     = var.backend_port
    protocol    = "tcp"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    {
      Name = local.name_backend_sg
    },
    var.tags
  )
}