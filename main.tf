locals {
  authorize_fn_name     = "${var.name_prefix}authorize-security-group-${var.secgroup_rule_type}"
  authorize_http_method = "POST"

  revoke_fn_name     = "${var.name_prefix}revoke-security-group-${var.secgroup_rule_type}"
  revoke_http_method = "DELETE"
}

resource "aws_api_gateway_rest_api" "manage_secgroup_ips_api" {
  name        = "terraform-aws-authenticating-secgroup"
  description = "${var.description}"
}

resource "aws_api_gateway_resource" "manage_secgroup_ips_endpoint" {
  rest_api_id = "${aws_api_gateway_rest_api.manage_secgroup_ips_api.id}"
  parent_id   = "${aws_api_gateway_rest_api.manage_secgroup_ips_api.root_resource_id}"
  path_part   = "connection"
}

module "python" {
  source          = "modules/python"

  type            = "${var.secgroup_rule_type}"
  security_groups = "${var.security_groups}"
  from_port       = "${var.secgroup_rule_from_port}"
  to_port         = "${var.secgroup_rule_to_port}"
  protocol        = "${var.secgroup_rule_protocol}"
  time_to_expire  = "${var.time_to_expire}"
}

// check out "api_*.tf"
