output "help" {
  value = "Resource Name Prefix is \"${var.name_prefix}\""
}

output "authorize_api" {
  value = {
    "method" = "${module.api_authorize.method}"
    "lambda_name" = "${module.api_authorize.lambda_name}"
    "execution_arn" =  "${module.api_authorize.execution_arn}"
    "invoke_url" =  "${module.api_authorize.invoke_url}"
  }
}
