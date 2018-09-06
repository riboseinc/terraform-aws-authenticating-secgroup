variable "description" {
  description = "Description of this secgroup"
  default     = "Dynamically Managing Security Group IPs API"
}

variable "name" {
  default = "terraform-aws-authenticating-secgroup"
  description = "Creates a unique name beginning with the specified prefix, useful for searching later"
}

variable "deployment_stage" {
  default     = "dev"
  description = "API deployment stages, ex: staging, production..."
}

variable "security_groups" {
  type        = "list"
  description = "Where to add the rules to"
}

variable "time_to_expire" {
  default     = 600
  description = "Time to expiry for every rule (in seconds)"
}

variable "log_level" {
  default = "INFO"
  description = "Set level of Cloud Watch Log to INFO or DEBUG"
}

variable "bucket_name" {}
