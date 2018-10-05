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


#### Provider config

- where should this API deployed to, more info https://www.terraform.io/docs/providers/aws

```hcl-terraform
provider "aws" {
  region  = "us-west-2"
}
```

#### Inline Config

```hcl-terraform
module "dynamic-secgroup" {
  source          = "../.."
  name            = "example-terraform-aws-authenticating-secgroup"
  description     = "example usage of terraform-aws-authenticating-secgroup"
  time_to_expire  = 120 # in seconds
  log_level = "DEBUG"

  # the module will load users in all json files in this bucket
  # sample "users.json"
  #     ["test_user1", "test_user1"]
  bucket_name = "your_users_json_bucket"

  security_groups = [
    {
      "group_ids"   = [
        "sg-df7a88a3",
        "sg-c9c72eb5"
      ],
      "rules"       = [
        {
          "type"      = "ingress",
          "from_port" = 44,
          "to_port"   = 44,
          "protocol"  = "tcp"
        }
      ],
      "region_name" = "us-west-2"
    },
    {
      "group_ids"   = [
        "sg-a1a9d8d8"
      ],
      "rules"       = [
        {
          "type"      = "ingress",
          "from_port" = 24,
          "to_port"   = 24,
          "protocol"  = "tcp"
        },
        {
          "type"      = "ingress",
          "from_port" = 25,
          "to_port"   = 25,
          "protocol"  = "tcp"
        }
      ],
      "region_name" = "us-west-1"
    }
  ]
}
```


#### Policy Config

```hcl-terraform
resource "aws_iam_policy" "this" {
  description = "Policy Developer SSH Access"
  policy      = "${data.aws_iam_policy_document.access_policy_doc.json}"
}

data "aws_iam_policy_document" "access_policy_doc" {
  statement {
    effect    = "Allow"

    actions   = [
      "execute-api:Invoke"
    ]

    resources = [
      "${module.dynamic-secgroup.execution_resources}"
    ]
  }
}
```

#### Some outputs

```hcl-terraform
output "dynamic-secgroup-api-invoke-url" {
  value = "${module.dynamic-secgroup.invoke_url}"
}
```

### Bash to execute the API
Check out [aws-authenticating-secgroup-scripts](https://github.com/riboseinc/aws-authenticating-secgroup-scripts)
