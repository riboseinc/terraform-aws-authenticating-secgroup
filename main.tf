locals {
  authorize_fn_name     = "authorize-${var.name}"
  authorize_http_method = "POST"

  revoke_fn_name        = "revoke-${var.name}"
  revoke_http_method    = "DELETE"

  clear_fn_name         = "clear-${var.name}"
  clear_event_rule_name = "clear-expired-ips-${var.name}"
  clear_event_rate      = "rate(1 minute)"

}

resource "aws_api_gateway_rest_api" "this" {
  name        = "${var.name}"
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

resource "aws_cloudwatch_log_group" "this" {
  depends_on = [
    "aws_api_gateway_rest_api.this"]
  name       = "API-Gateway-Execution-Logs_${aws_api_gateway_rest_api.this.id}/${var.deployment_stage}"
}

resource "aws_api_gateway_method_settings" "this" {
  depends_on  = [
    "aws_api_gateway_deployment.this",
    "aws_api_gateway_account.this"
  ]

  rest_api_id = "${aws_api_gateway_rest_api.this.id}"
  stage_name  = "${var.deployment_stage}"
  method_path = "*/*"

  settings {
    metrics_enabled    = true
    logging_level      = "INFO"
    data_trace_enabled = true
  }
}

module "python" {
  source          = "modules/python"
  log_level       = "${var.log_level}"
  security_groups = "${var.security_groups}"
  time_to_expire  = "${var.time_to_expire}"
  bucket_name = "${var.bucket_name}"
}

/**** check out "api_*.tf" ****/
