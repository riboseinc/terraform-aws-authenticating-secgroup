output "invoke_url" {
  value = "${aws_api_gateway_deployment.this.invoke_url}${aws_api_gateway_resource.this.path}"
}

output "execution_resources" {
  value = [
    "${module.gateway_authorize.execution_resource}",
    "${module.gateway_revoke.execution_resource}"
  ]
}

output "lambda_names" {
  value = [
    "${module.lamda_authorize.fn_name}",
    "${module.lamda_revoke.fn_name}",
    "${module.lamda_clear.fn_name}"
  ]
}

output "events" {
  value = [
    "${aws_cloudwatch_event_rule.clear.arn}"
  ]
}
