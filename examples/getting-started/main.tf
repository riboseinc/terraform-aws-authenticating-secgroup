variable "aws_account_id" {}
variable "aws_access_key" {}
variable "aws_secret_key" {}
variable "aws_region" {}
variable "description" {}

//module "dynamic-secgroup" {
//  source         = "modules/dynamic-secgroup"
//  description    = "${var.description}"
//
//  aws_account_id = "${var.aws_account_id}"
//  aws_access_key = "${var.aws_access_key}"
//  aws_region     = "${var.aws_region}"
//  aws_secret_key = "${var.aws_secret_key}"
//}

module "dynamic-secgroup" {
  source                  = "../../"
//  name_prefix             = "getting-started-"

//  aws_account_id          = "${var.aws_account_id}"
//  aws_region              = "us-west-2"
//
  # Description of this secgroup
//  description             = "${var.description}"

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
  time_to_expire          = 600

  security_groups = [
    {
      group_ids      = [
        "sg-df7a88a3",
        "sg-c9c72eb5"
      ]

      rules          = [
        {
          secgroup_rule_type      = "ingress"
          secgroup_rule_from_port = 22
          secgroup_rule_to_port   = 22
          secgroup_rule_protocol  = "tcp"
        },
        {
          secgroup_rule_type      = "ingress"
          secgroup_rule_from_port = 443
          secgroup_rule_to_port   = 443
          secgroup_rule_protocol  = "tcp"
        }
      ]
    },
  ]
}

resource "aws_iam_policy" "this" {
//  name        = "secgroup-access-policy"
  description = "Policy: ${var.description}"
  policy      = "${data.aws_iam_policy_document.access_policy_doc.json}"
}

data "aws_iam_policy_document" "access_policy_doc" {
  statement {
    effect    = "Allow"
    actions   = [
      "execute-api:Invoke"
    ]
    resources = ["${module.dynamic-secgroup.execution_resources}"]
  }
}

//module "access-policy" {
//  source              = "modules/access-policy"
//  description         = "Policy: ${var.description}"
//  execution_resources = "${module.dynamic-secgroup.dynamic-secgroup-api-execution-resources}"
//}

//output "dynamic-secgroup-api-invoke-url" {
//  value = "${module.dynamic-secgroup.dynamic-secgroup-api-invoke-url}"
//}
//
//output "dynamic-secgroup-api-excutions" {
//  value = "${module.dynamic-secgroup.dynamic-secgroup-api-execution-resources}"
//}
//
//output "api-gateway-access-policy-arn" {
//  value = "${module.access-policy.access-policy-arn}"
//}
