/** Lambda Role */
data "aws_iam_policy_document" "lambda_policy" {
  statement {
    effect  = "Allow",
    actions = [
      "sts:AssumeRole",
    ]

    principals {
      type        = "Service"
      identifiers = [
        "lambda.amazonaws.com"
      ]
    }
  }
}

data "aws_iam_policy_document" "ec2_policy" {
  statement {
    effect    = "Allow",
    actions   = [
      "ec2:DescribeSecurityGroups",
      "ec2:RevokeSecurityGroupIngress",
      "ec2:AuthorizeSecurityGroupEgress",
      "ec2:AuthorizeSecurityGroupIngress",
      "ec2:UpdateSecurityGroupRuleDescriptionsEgress",
      "ec2:RevokeSecurityGroupEgress",
      "ec2:UpdateSecurityGroupRuleDescriptionsIngress"
    ]
    resources = [
      "*"
    ]
  }
}

resource "aws_iam_role_policy" "ec2_role_policy" {
  name_prefix = "${var.name_prefix}"
  role        = "${aws_iam_role.lambda_sts_role.id}"
  policy      = "${data.aws_iam_policy_document.ec2_policy.json}"
}

resource "aws_iam_role" "lambda_sts_role" {
  name_prefix        = "${var.name_prefix}"
  description        = "to invoke lambda: ${local.fn_name}"
  assume_role_policy = "${data.aws_iam_policy_document.lambda_policy.json}"
}

/** API Gateway Role */
//data "aws_iam_policy_document" "gateway_policy" {
//  statement {
//    effect  = "Allow",
//    actions = [
//      "sts:AssumeRole",
//    ]
//
//    principals {
//      type        = "Service"
//      identifiers = [
//        "apigateway.amazonaws.com"
//      ]
//    }
//  }
//}
//
//resource "aws_iam_role" "gateway_sts_role" {
//  assume_role_policy = "${data.aws_iam_policy_document.lambda_policy.json}"
//}

