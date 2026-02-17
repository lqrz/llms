resource "aws_eip" "this" {
  domain = "vpc"

  tags = merge(
    {
      Name = "${var.name_prefix}-nat-eip"
    },
    var.tags
  )
}