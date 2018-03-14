/* Authorize API */
module "lamda_authorize" {
  source                = "modules/lambda"
  name                  = "${local.authorize_fn_name}"
  description = "${var.description}"
  handler               = "${module.python.authorize_handler}"
  role_arn              = "${module.sts_lambda.arn}"
  zip_path              = "${module.python.path}"
  zip_path_base64sha256 = "${module.python.path_base64sha256}"
}

module "gateway_authorize" {
  source            = "modules/api_gateway"
  deployment_stage  = "${var.deployment_stage}"

  lambda_fn_name    = "${module.lamda_authorize.fn_name}"
  lambda_invoke_arn = "${module.lamda_authorize.invoke_arn}"

  rest_api_id       = "${aws_api_gateway_rest_api.this.id}"
  resource_id       = "${aws_api_gateway_resource.this.id}"
  path              = "${aws_api_gateway_resource.this.path}"
  method            = "${local.authorize_http_method}"
}
