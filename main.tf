locals {
  authorize_fn_name     = "${var.name_prefix}authorize-secgroups"
  authorize_http_method = "POST"

  revoke_fn_name        = "${var.name_prefix}revoke-secgroups"
  revoke_http_method    = "DELETE"

  clear_fn_name         = "${var.name_prefix}clear-secgroups"
  clear_event_rule_name = "${var.name_prefix}clear-expired-ip"
  clear_event_rate      = "rate(1 minute)"
}

resource "aws_api_gateway_rest_api" "this" {
  name        = "${var.name_prefix}terraform-aws-authenticating-secgroup"
  description = "${var.description}"
}

resource "aws_api_gateway_resource" "this" {
  rest_api_id = "${aws_api_gateway_rest_api.this.id}"
  parent_id   = "${aws_api_gateway_rest_api.this.root_resource_id}"
  path_part   = "connection"
}

resource "aws_api_gateway_deployment" "this" {
  depends_on  = [
    "module.gateway_authorize",
    "module.gateway_revoke"
  ]

  rest_api_id = "${aws_api_gateway_rest_api.this.id}"
  stage_name  = "${var.deployment_stage}"
}

resource "aws_api_gateway_account" "this" {
  cloudwatch_role_arn = "${module.sts_gateway.arn}"
}

resource "aws_api_gateway_method_settings" "this" {
  depends_on  = ["aws_api_gateway_deployment.this", "aws_api_gateway_account.this"]
  rest_api_id = "${aws_api_gateway_rest_api.this.id}"
  stage_name  = "${var.deployment_stage}"
  method_path = "*/*"

  settings {
    metrics_enabled = true
    logging_level = "INFO"
    data_trace_enabled = true
  }
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


/**** check out "api_*.tf" ****/
