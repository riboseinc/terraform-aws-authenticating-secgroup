locals {
  uuid = "${uuid()}"
}
resource "template_dir" "this" {
  source_dir      = "${path.module}/src"
  destination_dir = "${path.module}/.src/${local.uuid}"

  vars {
    type            = "${var.type}"
    security_groups = "${jsonencode(var.security_groups)}"
    from_port       = "${var.from_port}"
    to_port         = "${var.to_port}"
    protocol        = "${var.protocol}"
    time_to_expire  = "${var.time_to_expire}"
  }
}

data "archive_file" "service_py" {
  depends_on  = [
    "template_dir.this"
  ]
  type        = "zip"
  output_path = "${path.module}/.src/${local.uuid}.zip"
  source_dir  = "${template_dir.this.destination_dir}"
}
