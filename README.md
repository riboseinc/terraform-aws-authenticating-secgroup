# Terraform Module For Dynamically Managing Security Group IPs

This module is available on the [Terraform Registry](https://registry.terraform.io/modules/riboseinc/authenticating-secgroup)


### Components

    1. API Gateway that performs authorization.

    2. On-demand Lambda function (linked to API Gateway method `POST|DELETE /connection`): to add/remove rules on-demand

    3. Continuous Lambda function: to clean up expired rules


### On-demand Lambda Function: Adding/Removing Rules

This is the Lambda function that runs `authorize-security-group-ingress` and
`revoke-security-group-ingress` on-demand on the given security group.

Steps:

    1.  Authenticate the user via AWS IAM (Signature Version 4).
        Eligibility to authenticate is set in a policy outside of this module.
        The user will provide an AWS v4 signature for authentication.
        Return **403** if not authorized.

    2. Once authenticated, Find out the source IP address (a host "/32").

    3. If the request is a `POST /connection`
        -   The function will add a `authorize-security-group-ingress` rule for this
            source IP address, with a description that indicates the "time" that this rule was added.
            Return **201**.
        -   If the source IP address is already in the security-group,
            update the description using `update-security-group-rule-descriptions-ingress` to reflect the latest time.
            Return **200**

    4. If the request is a `DELETE /connection`
        -   If the source IP address is in the security-group, issue a `revoke-security-group-ingress` on it. Return **200**.
        -   If the source IP address is not in the security group, do nothing. Return **404**.

    3. Done.

### Continuous Lambda Function: Removing Rules

This is the Lambda function that runs `revoke-security-group-ingress` on the
given security group on rule expiry.

This AWS Lambda function runs every X seconds, and its sole task is to clean
out the security group that has stale rules.

Steps:

    1. The function will describe all rules in the given security group.

    2. For every rule, it will check the description for the time of last update.
        -   If the elapsed time is less than the configured X seconds, don't do anything.
        -   If the elapsed time is more than the configured X seconds, it means that the
            rule has expired, and it should execute `revoke-security-group-ingress` on it.
            (e.g., if all rules are expired, the security group should now contain no rules)

    3. Done.


### Sample Usage

Check out [examples](https://github.com/riboseinc/terraform-aws-authenticating-secgroup/tree/master/examples) for more details

```terraform
module "dynamic-secgroup" {
  source = "riboseinc/authenticating-secgroup/aws"

  // prefix string used in named resources
  name_prefix             = "getting-started-"

  aws_account_id          = "${var.aws_account_id}"
  aws_region              = "us-west-2"

  // Description of this secgroup
  description             = "${var.description}"

  // Where to add the rules to
  security-groups = [
    "${aws_security_group.instance_group_1_ssh.id}",
    "${aws_security_group.instance_group_2_ssh.id}"
  ]

  // Parameters for creating security group rules
  secgroup_rule_type      = "ingress"
  secgroup_rule_from_port = 22
  secgroup_rule_to_port   = 22
  secgroup_rule_protocol  = "tcp"

  // Time to expiry for every rule.
  // Default: 600 seconds.
  time_to_expire          = 600
}


/** Sample "terraform.tfvars" */

aws_account_id = "aws_account_id"
aws_access_key = "aws_access_key"
aws_secret_key = "aws_secret_key"
aws_region = "aws_region"
description  = "Developer SSH Access"


/** Some outputs */

output "dynamic-secgroup-api-invoke-url" {
  value = "${module.dynamic-secgroup.invoke_url}"
}

output "dynamic-secgroup-api-execution-resources" {
  value = "${module.dynamic-secgroup.execution_resources}"
}
```


The `module.access-policy` is something like:

```terraform
resource "aws_iam_policy" "access_policy" {
  name = "secgroup-access-policy"
  description = "Policy: ${var.description}"
  policy      = "${data.aws_iam_policy_document.access_policy_doc.json}"
}

data "aws_iam_policy_document" "access_policy_doc" {
  statement {
    effect    = "Allow"
    actions   = [
      "execute-api:Invoke"
    ]
    resources = [
      "${var.execution_resources}"
    ]
  }
}

output "access-policy-arn" {
  value = "${aws_iam_policy.access_policy.arn}"
}
```

### Bash to execute the API
Check out [aws-authenticating-secgroup-scripts](https://github.com/phuonghuynh/aws-authenticating-secgroup-scripts)
