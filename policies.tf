module "sts_lambda" {
  source = "modules/sts_assume_role"

  service_identifier = "lambda.amazonaws.com"
  name = "${var.name}-lambda"
  actions = [
    "ec2:DescribeSecurityGroups",
    "ec2:RevokeSecurityGroupIngress",
    "ec2:AuthorizeSecurityGroupEgress",
    "ec2:AuthorizeSecurityGroupIngress",
    "ec2:UpdateSecurityGroupRuleDescriptionsEgress",
    "ec2:RevokeSecurityGroupEgress",
    "ec2:UpdateSecurityGroupRuleDescriptionsIngress",

    "s3:GetBucketLocation",
    "s3:ListBucket",
    "s3:GetObject",

    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ]
  description = "used by Lambda invoke EC2 Security Group"
}

module "sts_gateway" {
  source = "modules/sts_assume_role"

  service_identifier = "apigateway.amazonaws.com"
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
  description = "used by API Gateway to write log (CloudWatch)"
}
