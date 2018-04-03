provider "aws" {
  region  = "us-west-2"
}

module "dynamic-secgroup" {
  source          = "../.."

  name            = "example-terraform-aws-authenticating-secgroup"

  # Description of this secgroup
  description     = "example usage of terraform-aws-authenticating-secgroup"

  //  # Time to expiry for every rule.
  time_to_expire  = 600

  security_groups = [
    {
      "group_ids"   = [
        "sg-df7a88a3",
        "sg-c9c72eb5"
      ],
      "rules"       = [
        {
          "type"      = "ingress",
          "from_port" = 22,
          "to_port"   = 22,
          "protocol"  = "tcp"
        }
      ],
      "region_name" = "us-west-2"
    },
    {
      "group_ids"   = [
        "sg-c9c72eb5"
      ],
      "rules"       = [
        {
          "type"      = "ingress",
          "from_port" = 24,
          "to_port"   = 24,
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
