locals {
  fn_name     = "${var.name_prefix}revoke-security-group-${var.type}"
  http_method = "DELETE"
}

module "python" {
  source          = "../tools/python"

  type            = "${var.type}"
  security_groups = "${var.security_groups}"
  from_port       = "${var.from_port}"
  to_port         = "${var.to_port}"
  protocol        = "${var.protocol}"
  time_to_expire  = "${var.time_to_expire}"
}

module "lamda" {
  source                = "../tools/lambda"
  name                  = "${local.fn_name}"
  handler               = "${module.python.authorize_handler}"
  role_arn              = "${aws_iam_role.lambda_sts_role.arn}"
  zip_path              = "${module.python.path}"
  zip_path_base64sha256 = "${module.python.path_base64sha256}"
}

module "gateway" {
  source            = "../tools/api_gateway"
  aws_account_id    = "${var.aws_account_id}"
  aws_region        = "${var.aws_region}"
  name_prefix       = "${var.name_prefix}"

  lambda_fn_name    = "${module.lamda.fn_name}"
  lambda_invoke_arn = "${module.lamda.invoke_arn}"

  rest_api_id       = "${var.gateway_rest_api_id}"
  resource_id       = "${var.gateway_resource_id}"
  method            = "${local.http_method}"
  path              = "${var.gateway_http_path}"
}
