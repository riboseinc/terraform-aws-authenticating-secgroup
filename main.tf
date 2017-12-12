resource "aws_api_gateway_rest_api" "manage_secgroup_ips_api" {
  name        = "terraform-aws-authenticating-secgroup"
  description = "${var.description}"
}

resource "aws_api_gateway_resource" "manage_secgroup_ips_endpoint" {
  rest_api_id = "${aws_api_gateway_rest_api.manage_secgroup_ips_api.id}"
  parent_id   = "${aws_api_gateway_rest_api.manage_secgroup_ips_api.root_resource_id}"
  path_part   = "connection"
}

module "api_authorize" {
  source                   = "modules/api_authorize"

  gateway_rest_api_id      = "${aws_api_gateway_rest_api.manage_secgroup_ips_api.id}"
  gateway_resource_id      = "${aws_api_gateway_resource.manage_secgroup_ips_endpoint.id}"
  gateway_http_path        = "${aws_api_gateway_resource.manage_secgroup_ips_endpoint.path}"
  gateway_deployment_stage = "${var.deployment_stage}"

  aws_account_id           = "${var.aws_account_id}"
  aws_region               = "${var.aws_region}"

  type                     = "${var.secgroup_rule_type}"
  security_groups          = "${var.security_groups}"
  to_port                  = "${var.secgroup_rule_to_port}"
  from_port                = "${var.secgroup_rule_from_port}"
  protocol                 = "${var.secgroup_rule_protocol}"
  time_to_expire           = "${var.time_to_expire}"
}

module "api_revoke" {
  source                   = "modules/api_revoke"

  gateway_rest_api_id      = "${aws_api_gateway_rest_api.manage_secgroup_ips_api.id}"
  gateway_resource_id      = "${aws_api_gateway_resource.manage_secgroup_ips_endpoint.id}"
  gateway_http_path        = "${aws_api_gateway_resource.manage_secgroup_ips_endpoint.path}"
  gateway_deployment_stage = "${var.deployment_stage}"

  aws_account_id           = "${var.aws_account_id}"
  aws_region               = "${var.aws_region}"

  type                     = "${var.secgroup_rule_type}"
  security_groups          = "${var.security_groups}"
  to_port                  = "${var.secgroup_rule_to_port}"
  from_port                = "${var.secgroup_rule_from_port}"
  protocol                 = "${var.secgroup_rule_protocol}"
}
