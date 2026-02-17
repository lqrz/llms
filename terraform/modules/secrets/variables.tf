variable "name_prefix" {
  type        = string
  description = "Prefix for Name tags on all resources."
}

variable "tags" {
  type        = map(string)
  description = "Additional tags to apply to resources."
}
