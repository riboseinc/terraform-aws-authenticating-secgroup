output "invoke_urls" {
  value = [
    "${module.gateway_authorize.invoke_url}",
    "${module.gateway_revoke.invoke_url}"
  ]
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
    "${module.lamda_revoke.fn_name}"
  ]
}
