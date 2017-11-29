locals {
  execute_api_arn = "arn:aws:execute-api:${var.aws_region}:${var.aws_account_id}:${var.rest_api_id}/*/${var.method}${var.path}"
}

resource "aws_api_gateway_method" "method" {
  rest_api_id   = "${var.rest_api_id}"
  resource_id   = "${var.resource_id}"
  http_method   = "${var.method}"
  authorization = "AWS_IAM"
}

resource "aws_api_gateway_integration" "integration" {
  rest_api_id             = "${var.rest_api_id}"
  resource_id             = "${var.resource_id}"
  http_method             = "${aws_api_gateway_method.method.http_method}"
  type                    = "AWS_PROXY"

  uri                     = "${var.lambda_invoke_arn}"

  # AWS lambdas can only be invoked with the POST method
  integration_http_method = "POST"
}

resource "aws_api_gateway_method_response" "method_response" {
  rest_api_id     = "${var.rest_api_id}"
  resource_id     = "${var.resource_id}"
  http_method     = "${aws_api_gateway_method.method.http_method}"
  status_code     = "200"
}

resource "aws_api_gateway_integration_response" "integration_response" {
  depends_on         = [
    "aws_api_gateway_integration.integration"
  ]

  rest_api_id        = "${var.rest_api_id}"
  resource_id        = "${var.resource_id}"
  http_method        = "${aws_api_gateway_method.method.http_method}"
  status_code        = "200"
}

resource "aws_lambda_permission" "lambda_permission" {
  function_name = "${var.lambda_fn_name}"
  statement_id  = "AllowExecutionFromApiGateway"
  action        = "lambda:InvokeFunction"
  principal     = "apigateway.amazonaws.com"

  # More: http://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-control-access-using-iam-policies-to-invoke-api.html
  source_arn    = "${local.execute_api_arn}"
}

resource "aws_api_gateway_deployment" "deployment" {
  depends_on  = [
    "aws_api_gateway_integration_response.integration_response",
    "aws_lambda_permission.lambda_permission"
  ]

  rest_api_id = "${var.rest_api_id}"
  stage_name  = "${var.deployment_stage}"
}
