provider "aws" {
  region  = "us-west-2"
}

module "dynamic-secgroup" {
  source          = "../.."
  name            = "example-secgroup-inline"
  description     = "example usage of terraform-aws-authenticating-secgroup (inline)"
  time_to_expire  = 120
  log_level = "DEBUG"
  bucket_name = "test-secgroup"
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

output "dynamic-secgroup-api-invoke-url" {
  value = "${module.dynamic-secgroup.invoke_url}"
}
