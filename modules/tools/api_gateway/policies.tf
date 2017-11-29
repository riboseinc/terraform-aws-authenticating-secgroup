resource "aws_iam_policy" "access_policy" {
  name_prefix = "${var.name_prefix}"
  policy      = "${data.aws_iam_policy_document.access_policy_doc.json}"
}

data "aws_iam_policy_document" "access_policy_doc" {
  statement {
    effect    = "Allow"
    actions   = [
      "execute-api:Invoke"
    ]
    resources = [
      "${local.execute_api_arn}"
    ]
  }
}
