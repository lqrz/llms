variable "aws_region" {
  type = string
  description = "AWS region."
}

variable "name_prefix" {
  type        = string
  description = "Prefix for Name tags on all resources."
}

variable "project" {
  type        = string
  description = "Project tag value."
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC."
}

variable "enable_dns_support" {
  type        = bool
  description = "Whether to enable DNS support in the VPC."
}

variable "enable_dns_hostnames" {
  type        = bool
  description = "Whether to enable DNS hostnames in the VPC."
}

variable "availability_zone_configs" {
  description = "Per-AZ subnet config."
  type = map(object({
    public_cidr  = string
    private_cidr = string
  }))
}

# variable "ami_id" {
#   type        = string
#   description = "AMI ID for the webserver instance."
# }

# variable "instance_type" {
#   type        = string
#   description = "EC2 instance type for the webserver."
# }

# variable "instance_volume_size" {
#   type = number
#   description = "EC2 instance volume size."
# }

variable "frontend_health_path" {
  type = string
  description = "Frontend health path."
}

variable "frontend_container_image_uri" {
  type = string
  description = "Frontend ECR container image URI (w/ tag)."
}

variable "ecs_frontend_desired_count" {
  type = number
  description = "ECS frontend service desired count."
}

variable "frontend_port" {
  type = number
  description = "Frontend listening port."
}

variable "frontend_envvars" {
  type = map(string)
  description = "Frontend environment variables."
}

variable "backend_health_path" {
  type = string
  description = "Backend health path."
}

variable "backend_container_image_uri" {
  type = string
  description = "Backend ECR container image URI (w/ tag)."
}

variable "ecs_backend_desired_count" {
  type = number
  description = "ECS backend service desired count."
}

variable "backend_port" {
  type = number
  description = "Backend listening port."
}

variable "backend_envvars" {
  type = map(string)
  description = "Backend environment variables."
}

variable "ecr_repository_names" {
  type = list(string)
  description = "Short name for the ECR repository (suffix in Name tag)."
}

variable "image_tag_mutability" {
  type        = string
  description = "Image tag mutability setting (MUTABLE or IMMUTABLE)."
  default     = "MUTABLE"
}

variable "scan_on_push" {
  type = bool
  description = "Whether to enable image scanning on push."
}

variable "ecs_task_cpu" {
  type = number
  description = "ECS task cpu."
}

variable "ecs_task_memory" {
  type = number
  description = "ECS task memory."
}

variable "ecs_enable_container_insights" {
  type        = bool
  description = "Whether to enable CloudWatch Container Insights."
}

variable "secret_keys" {
  type = list(string)
  description = "API keys secret names list."
}

variable "tags" {
  type        = map(string)
  description = "Additional tags to apply to resources."
}
