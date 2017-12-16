locals {
  authorize_fn_name     = "authorize-security-group-${var.secgroup_rule_type}"
  authorize_http_method = "POST"

  revoke_fn_name        = "revoke-security-group-${var.secgroup_rule_type}"
  revoke_http_method    = "DELETE"

  clear_fn_name         = "clear-security-group-${var.secgroup_rule_type}"
}

resource "aws_api_gateway_rest_api" "this" {
  name        = "terraform-aws-authenticating-secgroup"
  description = "${var.description}"
}

resource "aws_api_gateway_resource" "this" {
  rest_api_id = "${aws_api_gateway_rest_api.this.id}"
  parent_id   = "${aws_api_gateway_rest_api.this.root_resource_id}"
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

resource "aws_api_gateway_deployment" "this" {
  depends_on  = [
    "module.gateway_authorize",
    "module.gateway_revoke"
  ]

  rest_api_id = "${aws_api_gateway_rest_api.this.id}"
  stage_name  = "${var.deployment_stage}"
}

/** check out "api_*.tf" */
