output "execution_resources" {
  value = [
    "${module.api_authorize.execution_resource}",
    "${module.api_revoke.execution_resource}"
  ]
}

output "invoke_urls" {
  value = [
    "${module.api_authorize.invoke_url}",
    "${module.api_revoke.invoke_url}"
  ]
}
