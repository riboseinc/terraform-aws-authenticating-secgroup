data "aws_iam_policy_document" "sts" {
  statement {
    effect  = "Allow",
    actions = [
      "sts:AssumeRole"
    ]

    principals {
      type        = "Service"
      identifiers = [
        "${var.service_identifier}"
      ]
    }
  }
}

data "aws_iam_policy_document" "this" {
  statement {
    effect    = "Allow",
    actions = "${var.actions}"
    resources = [
      "*"
    ]
  }
}

resource "aws_iam_role_policy" "this" {
  name_prefix = "${var.name_prefix}"
  role        = "${aws_iam_role.this.id}"
  policy      = "${data.aws_iam_policy_document.this.json}"
}

resource "aws_iam_role" "this" {
  name_prefix        = "${var.name_prefix}"
  description        = "${var.description}"
  assume_role_policy = "${data.aws_iam_policy_document.sts.json}"
}

