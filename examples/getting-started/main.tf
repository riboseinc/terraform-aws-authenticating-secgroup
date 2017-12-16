variable "aws_account_id" {}
variable "aws_access_key" {}
variable "aws_secret_key" {}
variable "aws_region" {}
variable "description" {}

module "dynamic-secgroup" {
  source         = "modules/dynamic-secgroup"
  description    = "${var.description}"

  aws_account_id = "${var.aws_account_id}"
  aws_access_key = "${var.aws_access_key}"
  aws_region     = "${var.aws_region}"
  aws_secret_key = "${var.aws_secret_key}"
}

module "access-policy" {
  source              = "modules/access-policy"
  description         = "Policy: ${var.description}"
  execution_resources = "${module.dynamic-secgroup.dynamic-secgroup-api-execution-resources}"
}

output "dynamic-secgroup-api-invoke-url" {
  value = "${module.dynamic-secgroup.dynamic-secgroup-api-invoke-url}"
}

output "dynamic-secgroup-api-excutions" {
  value = "${module.dynamic-secgroup.dynamic-secgroup-api-execution-resources}"
}

output "api-gateway-access-policy-arn" {
  value = "${module.access-policy.access-policy-arn}"
}
