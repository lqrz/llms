resource "aws_nat_gateway" "this" {
  allocation_id = aws_eip.this.id
  subnet_id     = aws_subnet.public.id

  tags = merge(
    {
      Name = "${var.name_prefix}-nat-gw"
    },
    var.tags
  )
}