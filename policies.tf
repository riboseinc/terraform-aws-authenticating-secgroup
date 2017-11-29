//resource "aws_iam_policy" "access_policy" {
//  //  name   = "access_policy"
//  description = "terraform-aws-authenticating-secgroup"
//  policy      = "${data.aws_iam_policy_document.access_policy_doc.json}"
//}
//
//data "aws_iam_policy_document" "access_policy_doc" {
////  policy_id = "ssh-access-policy"
//
//  statement {
////    sid       = "AccessSecurityGroup"
//    effect    = "Allow"
//    actions   = [
//      "execute-api:Invoke"
//    ]
//    resources = [
//      //      "arn:aws:execute-api:${var.aws-region}:${var.aws-account-id}:${aws_api_gateway_rest_api.api.name}/*/DELETE/connection",
//      //      "arn:aws:execute-api:${var.aws-region}:${var.aws-account-id}:${aws_api_gateway_rest_api.api.name}/*/POST/connection"
//    ]
//  }
//}
