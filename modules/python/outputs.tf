output "path" {
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

output "clear_handler" {
  value = "clear.handler"
}
