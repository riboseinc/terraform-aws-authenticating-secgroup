import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import time
import json
import helper


# args passed by module "terraform-aws-authenticating-secgroup"
handle_type = "${type}"
protocol = "${protocol}"

with helper.catch(ValueError): from_port = int("${from_port}")
with helper.catch(ValueError): to_port = int("${to_port}")
with helper.catch(ValueError): time_to_expire = int("${time_to_expire}")


class DynaSecGroups:

    def __init__(self, event=None):
        if handle_type not in ['ingress', 'egress']:
            raise OperationNotFoundError(f"Not found handler for type {handle_type.upper()}")

        self.security_groups = json.loads('${security_groups}')

        try:
            self.source_ip = event['requestContext']['identity']['sourceIp']
            self.cidr_ip = f'{self.source_ip}/32'
            self.sec_groups = [SecGroup(group_id=group_id, cidr_ip=self.cidr_ip) for group_id in self.security_groups]
        except KeyError as error:
            print(f"Ignore error {str(error)}")

    def __do_ingress_or_egress(self, ingress, egress):
        has_updated = True
        fail_groups = []
        for sec_group in self.sec_groups:
            has_updated = ingress(sec_group) if handle_type == 'ingress' else egress(sec_group)
            if not has_updated:
                fail_groups.append(sec_group.group.group_id)
        return has_updated, fail_groups

    def authorize(self):
        return self.__do_ingress_or_egress(
            lambda sg: sg.authorize_ingress(),
            lambda sg: sg.authorize_egress()
        )

    def revoke(self):
        return self.__do_ingress_or_egress(
            lambda sg: sg.revoke_ingress(),
            lambda sg: sg.revoke_egress()
        )


class SecGroup:

    def __init__(self, group_id, cidr_ip):
        ec2 = boto3.resource('ec2')
        group = ec2.SecurityGroup(group_id)
        group.load()

        self.cidr_ip = cidr_ip
        self.group = group
        self.client = self.group.meta.client

        # self.rule = rule

    def __populate_ip_permissions_args(self, expire=None):
        args = {
            "GroupId": self.group.group_id,
            "IpPermissions": [
                {
                    'FromPort': from_port,
                    'ToPort': to_port,
                    'IpProtocol': protocol,
                    'IpRanges': [
                        {
                            'CidrIp': self.cidr_ip
                            # 'Description': f'{expire.isoformat()}{time.strftime("%z")}'
                        }
                    ]
                }
            ]
        }

        if expire is not None:
            args['IpPermissions'][0]['IpRanges'][0]['Description'] = f'{expire.isoformat()}{time.strftime("%z")}'

        return args

    def __authorize(self, fn_authorize, fn_update):
        now = datetime.now()
        expire = now + timedelta(0, time_to_expire)
        ip_permissions = self.__populate_ip_permissions_args(expire=expire)

        try:
            fn_authorize(ip_permissions)
            return True
        except Exception as error:
            if not isinstance(error, ClientError):
                raise error

            error_code = error.response['Error']['Code']
            if error_code == 'InvalidPermission.Duplicate':
                fn_update(ip_permissions)
            else:
                raise error
        return False

    def authorize_ingress(self):
        return self.__authorize(
            lambda p: self.group.authorize_ingress(**p),
            lambda p: self.client.update_security_group_rule_descriptions_ingress(**p)
        )

    def authorize_egress(self):
        return self.__authorize(
            lambda p: self.group.authorize_egress(p),
            lambda p: self.client.update_security_group_rule_descriptions_egress(**p)
        )

    def __find_permission_by_rule(self, permissions):
        rule_set = {from_port, to_port, self.cidr_ip, protocol}
        for p in permissions:
            for ip_range in p['IpRanges']:
                p_set = {p['IpProtocol'], p['FromPort'], p['ToPort'], ip_range['CidrIp']}
                if rule_set == p_set:
                    return p, ip_range
        return None, None

    def revoke_ingress(self):
        permissions = self.group.ip_permissions
        permission, ip_range = self.__find_permission_by_rule(permissions)
        if permission is None:
            return False

        ip_permissions = self.__populate_ip_permissions_args()
        response = self.group.revoke_ingress(**ip_permissions)
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        return status_code < 400

    def revoke_egress(self):
        raise OperationNotFoundError(f"Revoke Egress IPs not supported atm")