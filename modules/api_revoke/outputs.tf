output "method" {
  value = "${local.http_method}"
}

output "invoke_url" {
  value = "${module.gateway.invoke_url}"
}

output "execution_resource" {
  value = "${module.gateway.execution_resource}"
}

output "lambda_name" {
  value = "${module.lamda.fn_name}"
}
