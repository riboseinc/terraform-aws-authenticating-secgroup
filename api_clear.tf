/* Clear expired Ip API */
module "lamda_clear" {
  source                = "modules/lambda"
  name                  = "${local.clear_fn_name}"
  description           = "Clear expired source_ips in security_groups ${jsonencode(var.security_groups)}"
  handler               = "${module.python.authorize_handler}"
  role_arn              = "${aws_iam_role.lambda_sts_role.arn}"
  zip_path              = "${module.python.path}"
  zip_path_base64sha256 = "${module.python.path_base64sha256}"
}


resource "aws_cloudwatch_event_rule" "clear" {
  depends_on          = [
    "module.lamda_clear"
  ]

  name                = "${var.name_prefix}-clear-expired-ip"
  description         = "clean up expired ips for groups ${jsonencode(var.security_groups)})"
  schedule_expression = "rate(1 minute)"
}

resource "aws_cloudwatch_event_target" "clear" {
  target_id = "${module.lamda_clear.id}"
  rule      = "${aws_cloudwatch_event_rule.clear.name}"
  arn       = "${module.lamda_clear.arn}"
  input     = "{${jsonencode("security_groups")}: ${jsonencode(var.security_groups)}}" //"${data.template_file.clear_input.rendered}"
}
