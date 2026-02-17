variable "aws_region" {
  type = string
  description = "AWS region."
}

variable "name_prefix" {
  type        = string
  description = "Prefix for Name tags on all resources."
}

variable "enable_container_insights" {
  type        = bool
  description = "Whether to enable CloudWatch Container Insights."
}

variable "vpc_id" {
  type        = string
  description = "VPC ID for the instance security group."
}

variable "subnet_ids" {
  type = list(string)
  description = "Subnet IDs."
}

variable "task_cpu" {
  type = number
  description = "Task cpu."
}

variable "task_memory" {
  type = number
  description = "Task memory."
}

variable "frontend_port" {
  type = number
  description = "Frontend listening port."
}

variable "frontend_container_image_uri" {
  type = string
  description = "Frontend ECR container image URI (w/ tag1)."
}

variable "frontend_desired_count" {
  type = number
  description = "Frontend service desired count."
}

variable "frontend_alb_target_group_arn" {
  type = string
  description = "Frontend ALB target group arn."
}

variable "frontend_security_group_id" {
  type = string
  description = "Frontend ALB security group ID."
}

variable "frontend_envvars" {
  type = map(string)
  description = "Frontend environment variables."
}

# --- backend

variable "backend_port" {
  type = number
  description = "Backend listening port."
}

variable "backend_container_image_uri" {
  type = string
  description = "Backend ECR container image URI (w/ tag1)."
}

variable "backend_desired_count" {
  type = number
  description = "Backend service desired count."
}

variable "backend_alb_target_group_arn" {
  type = string
  description = "Backend ALB target group arn."
}

variable "backend_security_group_id" {
  type = string
  description = "Backend ALB security group ID."
}

variable "backend_url" {
  type = string
  description = "Backend url (w/ port)"
}

variable "backend_envvars" {
  type = map(string)
  description = "Backend environment variables."
}

variable "secrets_manager_arn" {
  type = string
  description = "Secret manager ARN."
}

variable "secret_keys" {
  type = list(string)
  description = "API keys secret names list."
}

variable "tags" {
  type        = map(string)
  description = "Additional tags to apply to resources."
}
