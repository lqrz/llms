variable "name_prefix" {
  type        = string
  description = "Prefix for Name tags on all resources."
}

variable "vpc_id" {
  type = string
  description = "ID of the created VPC."
}

variable "aws_availability_zone" {
  type = string
  description = "AWS availability zone to deploy into."
}

variable "public_subnet_cidr" {
  type = string
  description = "CIDR block for the public subnet."
}

variable "private_subnet_cidr" {
  type = string
  description = "CIDR block for the private subnet."
}

variable "internet_gateway_id" {
  type = string
  description = "Internet gateway ID."
}

variable "tags" {
  type        = map(string)
  description = "Additional tags to apply to resources."
}
