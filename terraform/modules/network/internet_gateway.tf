resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc.id

  tags = merge(
    {
      Name = "${var.name_prefix}-igw"
    },
    var.tags
  )
}
