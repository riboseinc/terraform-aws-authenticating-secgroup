variable "aws_account_id" {
  description = "AWS account id"
}

variable "aws_region" {
  description = "AWS region"
}

variable "description" {
  description = "Description of this secgroup"
  default = "Dynamically Managing Security Group IPs API"
}

variable "name_prefix" {
  default = "dyna-secgroup"
  description = "Creates a unique name beginning with the specified prefix, useful for searching later"
}

variable "deployment_stage" {
  default     = "dev"
  description = "Api deployment stages, ex: staging, production..."
}

variable "security_groups" {
  type        = "list"
  description = "Where to add the rules to"
}

variable "secgroup_rule_type" {
  default     = "ingress"
  description = "Parameters for creating security group rules, posible values: 'ingress', 'egress'"
}

variable "secgroup_rule_from_port" {
  default = 22
}

variable "secgroup_rule_to_port" {
  default = 22
}

variable "secgroup_rule_protocol" {
  default = "tcp"
}

variable "time_to_expire" {
  default     = 600
  description = "ime to expiry for every rule."
}

