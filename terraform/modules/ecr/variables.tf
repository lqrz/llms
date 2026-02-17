variable "name_prefix" {
  type        = string
  description = "Prefix for Name tags on all resources."
}

variable "repository_name" {
  type        = string
  description = "Short name for the ECR repository (suffix in Name tag)."
}

variable "image_tag_mutability" {
  type        = string
  description = "Image tag mutability setting (MUTABLE or IMMUTABLE)."
}

variable "scan_on_push" {
  type        = bool
  description = "Whether to enable image scanning on push."
}

variable "tags" {
  type        = map(string)
  description = "Additional tags to apply to resources."
}
