//variable "aws_account_id" {}
//variable "aws_access_key" {}
//variable "aws_secret_key" {}
//variable "aws_region" {}
//variable "description" {}
//
//module "dynamic-secgroup" {
//  source                  = "../../../.."
//  name_prefix             = "getting-started-"
//
//  aws_account_id          = "${var.aws_account_id}"
//  aws_region              = "us-west-2"
//
//  # Description of this secgroup
//  description             = "${var.description}"
//
//  # Where to add the rules to
//  security_groups         = [
//    "sg-df7a88a3",
//    "sg-c9c72eb5"
//  ]
//
//  # Parameters for creating security group rules
//  secgroup_rule_type      = "ingress"
//  secgroup_rule_from_port = 22
//  secgroup_rule_to_port   = 22
//  secgroup_rule_protocol  = "tcp"
//
//  # Time to expiry for every rule.
//  # Default: 600 seconds.
//  time_to_expire          = 600
//}

//output "dynamic-secgroup-api-invoke-url" {
//  value = "${module.dynamic-secgroup.invoke_url}"
//}
//
//output "dynamic-secgroup-api-execution-resources" {
//  value = "${module.dynamic-secgroup.execution_resources}"
//}
