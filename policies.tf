module "sts_lambda" {
  source = "modules/sts_assume_role"

  service_identifier = "lambda.amazonaws.com"
//  name_prefix = "${var.name_prefix}"
  name = "${var.name}-lambda"
  actions = [
    "ec2:DescribeSecurityGroups",
    "ec2:RevokeSecurityGroupIngress",
    "ec2:AuthorizeSecurityGroupEgress",
    "ec2:AuthorizeSecurityGroupIngress",
    "ec2:UpdateSecurityGroupRuleDescriptionsEgress",
    "ec2:RevokeSecurityGroupEgress",
    "ec2:UpdateSecurityGroupRuleDescriptionsIngress"
  ]
  description = "used by Lambda invoke Ec2 Security Group"
}

module "sts_gateway" {
  source = "modules/sts_assume_role"

  service_identifier = "apigateway.amazonaws.com"
  //name_prefix = "${var.name_prefix}"
  name = "${var.name}-gateway"
  actions = [
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:DescribeLogGroups",
    "logs:DescribeLogStreams",
    "logs:PutLogEvents",
    "logs:GetLogEvents",
    "logs:FilterLogEvents"
  ]
  description = "used by Api Gateway to write log (cloudwatch)"
}
