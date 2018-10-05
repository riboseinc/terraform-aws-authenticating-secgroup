variable "log_level" {
}

variable "security_groups" {
  type    = "list"
  default = []
}

variable "time_to_expire" {
  default = ""
}

variable "bucket_name" {}
