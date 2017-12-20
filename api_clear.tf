/* Clear expired Ip API */
module "lamda_clear" {
  source                = "modules/lambda"
  name                  = "${local.clear_fn_name}"
  description           = "Clear expired source_ips in ${var.secgroup_rule_type} security_groups"
  handler               = "${module.python.clear_handler}"
  role_arn              = "${aws_iam_role.lambda_sts_role.arn}"
  zip_path              = "${module.python.path}"
  zip_path_base64sha256 = "${module.python.path_base64sha256}"
}


resource "aws_cloudwatch_event_rule" "clear" {
  depends_on          = [
    "module.lamda_clear"
  ]

  name                = "${local.clear_event_rule_name}"
  description         = "clean up expired ips in security_groups"
  schedule_expression = "${local.clear_event_rate}"
}

resource "aws_cloudwatch_event_target" "clear" {
  rule = "${aws_cloudwatch_event_rule.clear.name}"
  arn  = "${module.lamda_clear.arn}"
}

resource "aws_lambda_permission" "clear" {
  function_name = "${module.lamda_clear.fn_name}"
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  principal     = "events.amazonaws.com"
  source_arn    = "${aws_cloudwatch_event_rule.clear.arn}"
}
