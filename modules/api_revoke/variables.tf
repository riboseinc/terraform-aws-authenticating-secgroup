variable "aws_region" {}
variable "aws_account_id" {}
variable "name_prefix" {}

variable "gateway_rest_api_id" {}
variable "gateway_resource_id" {}
variable "gateway_http_path" {}

variable "type" {}
variable "security_groups" {
  type = "list"
}
variable "from_port" {}
variable "to_port" {}
variable "protocol" {}
variable "time_to_expire" {}
