variable "name" {}
variable "handler" {}
variable "zip_path" {}
variable "zip_path_base64sha256" {}
variable "role_arn" {}
variable "description" {
  default = "created by terraform-aws-authenticating-secgroup"
}
