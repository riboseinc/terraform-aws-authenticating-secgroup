output "method" {
  value = "${local.http_method}"
}

output "invoke_url" {
  value = "${module.gateway.invoke_url}${var.gateway_http_path}"
}

output "execution_arn" {
  value = "${module.gateway.execution_arn}${var.gateway_http_path}"
}

output "lambda_name" {
  value = "${module.lamda.fn_name}"
}
