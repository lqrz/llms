
module "availability_zones" {
  source = "./submodules/availability_zone"
  for_each = var.availability_zone_configs

  name_prefix = "${var.name_prefix}-az-${each.key}"
  vpc_id = aws_vpc.vpc.id
  aws_availability_zone = each.key
  public_subnet_cidr = each.value.public_cidr
  private_subnet_cidr = each.value.private_cidr
  internet_gateway_id = aws_internet_gateway.igw.id
  tags = var.tags
}
