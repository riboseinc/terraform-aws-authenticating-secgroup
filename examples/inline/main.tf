provider "aws" {
  region  = "us-west-2"
}

module "dynamic-secgroup" {
  source          = "../.."
  name            = "example-secgroup-inline"
  description     = "example usage of terraform-aws-authenticating-secgroup (inline)"
  time_to_expire  = 120
  log_level = "DEBUG"
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
    }
  ]
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
      "${module.dynamic-secgroup.execution_resources}"
    ]
  }
}

output "dynamic-secgroup-api-invoke-url" {
  value = "${module.dynamic-secgroup.invoke_url}"
}
