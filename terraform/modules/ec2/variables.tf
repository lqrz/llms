variable "name_prefix" {
  type        = string
  description = "Prefix for Name tags on all resources."
}

variable "ami_id" {
  type        = string
  description = "AMI ID for the EC2 instance."
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type."
  default     = "t3.micro"
}

variable "subnet_id" {
  type        = string
  description = "Subnet ID where the instance will be placed."
}

variable "tags" {
  type        = map(string)
  description = "Additional tags to apply to resources."
}

variable "security_group_id" {
  type = string
  description = "EC2 instance security group id."
}

variable "instance_volume_size" {
  type = number
  description = "EC2 instance volume size."
}