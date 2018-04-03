provider "aws" {
  region  = "us-west-2"
}

module "dynamic-secgroup" {
  source          = "../../"

  name            = "example-json-secgroups"

  # Description of this secgroup
  description     = "example usage of terraform-aws-authenticating-secgroup"

  //  # Time to expiry for every rule.
  time_to_expire  = 600

  security_groups = ["${file("secgroups.json")}"]
}

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
      "${module.dynamic-secgroup.execution_resources}"]
  }
}

output "dynamic-secgroup-api-invoke-url" {
  value = "${module.dynamic-secgroup.invoke_url}"
}