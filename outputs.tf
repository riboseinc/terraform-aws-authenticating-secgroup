output "execution_resources" {
  value = [
    "${module.api_authorize.execution_resource}"
  ]
}

output "invoke_urls" {
  value = [
    "${module.api_authorize.invoke_url}"
  ]
}
