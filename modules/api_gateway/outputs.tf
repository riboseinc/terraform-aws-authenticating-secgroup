output "invoke_url" {
  value = "${aws_api_gateway_deployment.deployment.invoke_url}${var.path}"
}

output "execution_resource" {
  value = "${local.execute_api_arn}"
}
