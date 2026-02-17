output "vpc_id" {
  description = "ID of the created VPC."
  value       = aws_vpc.vpc.id
}

output "availability_zones"  {
  value = {
    for az, m in module.availability_zones : az => {
      public_subnet_id        = m.public_subnet_id
      private_subnet_id       = m.private_subnet_id
    }
  }
}
