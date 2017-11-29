output "invoke_url" {
  value = "${aws_api_gateway_deployment.deployment.invoke_url}"
}

output "execution_arn" {
  value = "${aws_api_gateway_deployment.deployment.execution_arn}"
}
