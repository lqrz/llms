locals {
  name_frontend = "${var.name_prefix}-front" 
  name_backend = "${var.name_prefix}-back" 
}

resource "aws_lb" "frontend" {
  name               = local.name_frontend
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.frontend.id]
  subnets            = var.public_subnet_ids

  tags = merge(
    {
      Name = local.name_frontend
    },
    var.tags
  )
}

resource "aws_lb" "backend" {
  name               = local.name_backend
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.backend.id]
  subnets            = var.private_subnet_ids

  tags = merge(
    {
      Name = local.name_backend
    },
    var.tags
  )
}
