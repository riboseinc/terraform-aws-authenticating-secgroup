output "fn_name" {
  value = "${aws_lambda_function.this.function_name}"
}

output "arn" {
  value = "${aws_lambda_function.this.arn}"
}

output "invoke_arn" {
  value = "${aws_lambda_function.this.invoke_arn}"
}

output "id" {
  value = "${aws_lambda_function.this.id}"
}
