//variable "type" {}

variable "security_groups" {
  type    = "list"
  default = []
}

//variable "from_port" {
//  default = ""
//}
//
//variable "to_port" {
//  default = ""
//}
//
//variable "protocol" {
//  default = ""
//}

variable "time_to_expire" {
  default = ""
}
