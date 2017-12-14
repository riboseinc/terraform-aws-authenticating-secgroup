output "fn_name" {
  value = "${aws_lambda_function.lambda_function.function_name}"
}

output "invoke_arn" {
  value = "${aws_lambda_function.lambda_function.invoke_arn}"
}
