resource "aws_lambda_function" "this" {
  description      = "${var.description}"
  role             = "${var.role_arn}"
  runtime          = "python3.6"

  filename         = "${var.zip_path}"
  source_code_hash = "${var.zip_path_base64sha256}"

  function_name    = "${var.name}"
  handler          = "${var.handler}"
}
