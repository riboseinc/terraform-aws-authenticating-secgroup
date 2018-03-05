///* Revoke API */
//module "lamda_revoke" {
//  source                = "modules/lambda"
//  name                  = "${local.revoke_fn_name}"
//  description           = "Removes source_ip from ${var.secgroup_rule_type} security_groups"
//  handler               = "${module.python.revoke_handler}"
//  role_arn              = "${module.sts_lambda.arn}"
//  zip_path              = "${module.python.path}"
//  zip_path_base64sha256 = "${module.python.path_base64sha256}"
//}
//
//module "gateway_revoke" {
//  source            = "modules/api_gateway"
//  deployment_stage  = "${var.deployment_stage}"
//
//  aws_account_id    = "${var.aws_account_id}"
//  aws_region        = "${var.aws_region}"
//  name_prefix       = "${var.name_prefix}"
//
//  lambda_fn_name    = "${module.lamda_revoke.fn_name}"
//  lambda_invoke_arn = "${module.lamda_revoke.invoke_arn}"
//
//  rest_api_id       = "${aws_api_gateway_rest_api.this.id}"
//  resource_id       = "${aws_api_gateway_resource.this.id}"
//  path              = "${aws_api_gateway_resource.this.path}"
//  method            = "${local.revoke_http_method}"
//}
