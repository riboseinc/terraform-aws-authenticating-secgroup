//variable "execution_resources" {
//  type = "list"
//}
//
//variable "description" {}
//
//resource "aws_iam_policy" "this" {
//  name        = "secgroup-access-policy"
//  description = "Policy: ${var.description}"
//  policy      = "${data.aws_iam_policy_document.access_policy_doc.json}"
//}
//
//data "aws_iam_policy_document" "access_policy_doc" {
//  statement {
//    effect    = "Allow"
//    actions   = [
//      "execute-api:Invoke"
//    ]
//    resources = [
//      "${var.execution_resources}"
//    ]
//  }
//}
//
//output "access-policy-arn" {
//  value = "${aws_iam_policy.this.arn}"
//}
