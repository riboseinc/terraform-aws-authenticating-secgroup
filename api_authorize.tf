/* Authorize API */
module "lamda_authorize" {
  source                = "modules/lambda"
  name                  = "${local.authorize_fn_name}"
  description           = "Adds source_ip to ${var.secgroup_rule_type} security_groups"
  handler               = "${module.python.authorize_handler}"
  role_arn              = "${aws_iam_role.lambda_sts_role.arn}"
  zip_path              = "${module.python.path}"
  zip_path_base64sha256 = "${module.python.path_base64sha256}"
}

module "gateway_authorize" {
  source            = "modules/api_gateway"
  deployment_stage  = "${var.deployment_stage}"

  aws_account_id    = "${var.aws_account_id}"
  aws_region        = "${var.aws_region}"
  name_prefix       = "${var.name_prefix}"

  lambda_fn_name    = "${module.lamda_authorize.fn_name}"
  lambda_invoke_arn = "${module.lamda_authorize.invoke_arn}"

  rest_api_id       = "${aws_api_gateway_rest_api.this.id}"
  resource_id       = "${aws_api_gateway_resource.this.id}"
  path              = "${aws_api_gateway_resource.this.path}"
  method            = "${local.authorize_http_method}"
}
