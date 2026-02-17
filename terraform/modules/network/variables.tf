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

variable "tags" {
  type        = map(string)
  description = "Additional tags to apply to resources."
}
