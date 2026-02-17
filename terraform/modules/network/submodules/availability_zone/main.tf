resource "aws_subnet" "public" {
  vpc_id            = var.vpc_id
  cidr_block        = var.public_subnet_cidr
  availability_zone = var.aws_availability_zone

  tags = merge(
    {
      Name = "${var.name_prefix}-public-subnet"
    },
    var.tags
  )
}

resource "aws_subnet" "private" {
  vpc_id            = var.vpc_id
  cidr_block        = var.private_subnet_cidr
  availability_zone = var.aws_availability_zone

  tags = merge(
    {
      Name = "${var.name_prefix}-private-subnet"
    },
    var.tags
  )
}
