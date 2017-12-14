/* Revoke API */
module "lamda_revoke" {
  source                = "modules/lambda"
  name                  = "${local.revoke_fn_name}"
  handler               = "${module.python.revoke_handler}"
  role_arn              = "${aws_iam_role.lambda_sts_role.arn}"
  zip_path              = "${module.python.path}"
  zip_path_base64sha256 = "${module.python.path_base64sha256}"
}

module "gateway_revoke" {
  source            = "modules/api_gateway"
  deployment_stage  = "${var.deployment_stage}"

  aws_account_id    = "${var.aws_account_id}"
  aws_region        = "${var.aws_region}"
  name_prefix       = "${var.name_prefix}"

  lambda_fn_name    = "${module.lamda_revoke.fn_name}"
  lambda_invoke_arn = "${module.lamda_revoke.invoke_arn}"

  rest_api_id       = "${aws_api_gateway_rest_api.manage_secgroup_ips_api.id}"
  resource_id       = "${aws_api_gateway_resource.manage_secgroup_ips_endpoint.id}"
  path              = "${aws_api_gateway_resource.manage_secgroup_ips_endpoint.path}"
  method            = "${local.revoke_http_method}"
}
