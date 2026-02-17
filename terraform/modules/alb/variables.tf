variable "name_prefix" {
  type        = string
  description = "Prefix for Name tags on all resources."
}

variable "tags" {
  type        = map(string)
  description = "Additional tags to apply to resources."
}

variable "vpc_id" {
  type        = string
  description = "VPC ID for the instance security group."
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "Public subnet IDs for the ALB."
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for the ALB."
}

variable "frontend_task_security_group_id" {
  type = string
  description = "Frontend task SG."
}

variable "frontend_health_path" {
  type = string
  description = "Frontend health path."
}

variable "frontend_port" {
  type = number
  description = "Frontend listening port."
}

variable "backend_health_path" {
  type = string
  description = "Backend health path."
}

variable "backend_port" {
  type = number
  description = "Backend listening port."
}

