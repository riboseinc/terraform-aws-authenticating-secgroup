module "dynamic-secgroup" {
  //  source = "riboseinc/authenticating-secgroup/aws"
  source                  = "../.."
  aws_account_id          = "${var.aws_account_id}"
  aws_region              = "us-west-2"

  # Description of this secgroup
  //  description             = "Developer SSH Access"

  # Where to add the rules to
  security_groups         = [
    "sg-df7a88a3",
    "sg-c9c72eb5"
    //    "${aws_security_group.instance_group_1_ssh.id}",
    //    "${aws_security_group.instance_group_2_ssh.id}"
  ]
  //  security_groups = "sg-df7a88a3,sg-c9c72eb5"

  # Parameters for creating security group rules
  //  secgroup_rule_type      = "ingress"
  secgroup_rule_from_port = 22
  secgroup_rule_to_port   = 22
  secgroup_rule_protocol  = "tcp"

  # Time to expiry for every rule.
  # Default: 600 seconds.
  time_to_expire          = 600
}

# A group we want to provide SSH access to
//resource "aws_iam_group" "developers" {
//  name = "developers"
//}

# Who can access this API (i.e., who can be added to the dynamic secgroup)
//resource "aws_iam_group_policy_attachment" "developers-access-ssh" {
//  group      = "${aws_iam_group.developers.name}"
//  policy_arn = "${module.dynamic-secgroup.api-gateway-access-policy-arn}"
//}


