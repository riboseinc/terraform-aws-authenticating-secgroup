locals {
  execute_api_arn = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${var.rest_api_id}/${var.deployment_stage}/${var.method}${var.path}"
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

resource "aws_api_gateway_method" "this" {
  rest_api_id   = "${var.rest_api_id}"
  resource_id   = "${var.resource_id}"
  http_method   = "${var.method}"
  authorization = "AWS_IAM"
}

resource "aws_api_gateway_integration" "this" {
  rest_api_id             = "${var.rest_api_id}"
  resource_id             = "${var.resource_id}"
  http_method             = "${aws_api_gateway_method.this.http_method}"
  type                    = "AWS_PROXY"

  uri                     = "${var.lambda_invoke_arn}"

  # AWS lambdas can only be invoked with the POST method
  integration_http_method = "POST"
}

resource "aws_api_gateway_method_response" "this" {
  rest_api_id = "${var.rest_api_id}"
  resource_id = "${var.resource_id}"
  http_method = "${aws_api_gateway_method.this.http_method}"
  status_code = "200"
}

resource "aws_api_gateway_integration_response" "this" {
  depends_on  = [
    "aws_api_gateway_integration.this"
  ]

  rest_api_id = "${var.rest_api_id}"
  resource_id = "${var.resource_id}"
  http_method = "${aws_api_gateway_method.this.http_method}"
  status_code = "200"
}

resource "aws_lambda_permission" "this" {
  function_name = "${var.lambda_fn_name}"
  statement_id  = "AllowExecutionFromApiGateway"
  action        = "lambda:InvokeFunction"
  principal     = "apigateway.amazonaws.com"

  # More: http://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-control-access-using-iam-policies-to-invoke-api.html
  source_arn    = "${local.execute_api_arn}"
}
