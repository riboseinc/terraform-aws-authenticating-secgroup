# Some outputs
//output "dynamic-secgroup-api-gateway-arn" {
//  value = "${module.dynamic-secgroup.api-gateway-arn}"
//}
//
//output "dynamic-secgroup-api-gateway-access-policy-arn" {
//  value = "${module.dynamic-secgroup.api-gateway-access-policy-arn}"
//}

//output "dynamic-secgroup-api-authorize-invoke" {
//  value = "${module.dynamic-secgroup.authorize_api_invoke}"
//}

output "help" {
  value = "${module.dynamic-secgroup.help}"
}

output "authorize_api" {
  value = "${module.dynamic-secgroup.authorize_api}"
}
