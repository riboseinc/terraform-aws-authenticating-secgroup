variable "aws_account_id" {}
variable "aws_region" {}
variable "name_prefix" {}

variable "rest_api_id" {}
variable "resource_id" {}
variable "method" {}
variable "path" {}

variable "lambda_fn_name" {}
variable "lambda_invoke_arn" {}

variable "deployment_stage" {
  default     = "dev"
}
