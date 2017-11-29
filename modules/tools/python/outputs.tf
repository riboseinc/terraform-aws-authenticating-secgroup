output "path" {
  depends_on = [ "archive_file.service_py" ]
  value = "${data.archive_file.service_py.output_path}"
}

output "path_base64sha256" {
  value = "${data.archive_file.service_py.output_base64sha256}"
}

output "authorize_handler" {
  value = "authorize.handler"
}

output "revoke_handler" {
  value = "revoke.handler"
}
