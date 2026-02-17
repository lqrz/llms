resource "aws_ecr_repository" "ecr" {
  name                 = "${var.name_prefix}/${var.repository_name}"
  image_tag_mutability = var.image_tag_mutability

  image_scanning_configuration {
    scan_on_push = var.scan_on_push
  }

  tags = merge(
    {
      Name = "${var.name_prefix}-${var.repository_name}"
    },
    var.tags
  )
}
