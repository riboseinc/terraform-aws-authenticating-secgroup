import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import time
import json
import helper
from dateutil import parser
from abc import ABC, abstractmethod

# args passed by module "terraform-aws-authenticating-secgroup"
handle_type = "${type}"
protocol = "${protocol}"

with helper.catch(ValueError): from_port = int("${from_port}")
with helper.catch(ValueError): to_port = int("${to_port}")
with helper.catch(ValueError): time_to_expire = int("${time_to_expire}")

expired_at = 'expired at {}'


class DynaSecGroups:

    def __init__(self, event=None):
        if handle_type not in ['ingress', 'egress']:
            raise helper.OperationNotSupportedError(f"Not found handler for type {handle_type.upper()}")

        self.security_groups = json.loads('${security_groups}')

        cidr_ip = None

        try:
            self.source_ip = event['requestContext']['identity']['sourceIp']

            cidr_ip = f'{self.source_ip}/32'
            self.cidr_ip = f'{self.source_ip}/32'
        except KeyError as error:
            print(f"Ignore error {str(error)}")

        self.sec_groups = [SecGroup(group_id=group_id, cidr_ip=cidr_ip) for group_id in self.security_groups]

    def __do_ingress_or_egress(self, ingress, egress):
        success = True  # empty group is OK because nothing tobe done
        fail_groups = []
        for sec_group in self.sec_groups:
            success = ingress(sec_group) if handle_type == 'ingress' else egress(sec_group)
            if not success:
                fail_groups.append(sec_group.group.group_id)
        return success, fail_groups

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

    def clear(self):
        return self.__do_ingress_or_egress(
            lambda sg: sg.clear_expired_ips_ingress(),
            lambda sg: sg.clear_expired_ips_egress()
        )


class SecGroup:

    def __init__(self, group_id, cidr_ip=None):
        ec2 = boto3.resource('ec2')
        group = ec2.SecurityGroup(group_id)
        group.load()

        self.cidr_ip = cidr_ip
        self.group = group
        self.client = self.group.meta.client

    def __populate_ip_permissions_args(self, **kwargs):
        # expire = None, ip_ranges = None
        expire = kwargs.get('expire', None)
        ip_ranges = kwargs.get('ip_ranges', [])

        args = {
            "GroupId": self.group.group_id,
            "IpPermissions": [{
                'FromPort': from_port,
                'ToPort': to_port,
                'IpProtocol': protocol
            }]
        }

        if self.cidr_ip is not None:
            ip_ranges.append(
                {'CidrIp': self.cidr_ip} if expire is None
                else {'CidrIp': self.cidr_ip, 'Description': expired_at.format(f'{expire.isoformat()}{time.strftime("%z")}')}
            )
        args['IpPermissions'][0]['IpRanges'] = ip_ranges
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
        # return self.__authorize(
        #     lambda p: self.group.authorize_egress(p),
        #     lambda p: self.client.update_security_group_rule_descriptions_egress(**p)
        # )
        raise helper.OperationNotSupportedError(f"Authorize Egress IPs not supported atm")

    def __find_permissions_by_args(self, flt):
        permissions = self.group.ip_permissions if handle_type == 'ingress' else self.group.ip_permissions_egress
        for p in permissions:
            for ip_range in p['IpRanges']:
                if flt(p, ip_range):
                    yield p, ip_range

    def __find_first_permission_by_args(self):
        try:
            rule_set = {from_port, to_port, self.cidr_ip, protocol}
            return next(self.__find_permissions_by_args(
                flt=lambda p, ip_range: rule_set == {p['FromPort'], p['ToPort'], ip_range['CidrIp'], p['IpProtocol']})
            )
        except StopIteration:
            return None, None

    def __revoke(self, revoke_fn):
        permission, ip_range = self.__find_first_permission_by_args()
        if permission is None:
            return False

        ip_permissions = self.__populate_ip_permissions_args()
        response = revoke_fn(
            ip_permissions)  # self.group.revoke_ingress(**ip_permissions)  # TODO can be used for revoke_egress also
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        return status_code < 400

    def revoke_ingress(self):
        return self.__revoke(lambda p: self.group.revoke_ingress(**p))

    def revoke_egress(self):
        raise helper.OperationNotSupportedError(f"Revoke Egress IPs not supported atm")

    def __clear(self, revoke_fn):
        now, rule_set = datetime.now().timestamp(), {from_port, to_port, protocol}
        revoke_ips, desc_prefix = [], expired_at.format("")

        for p, ip_range in self.__find_permissions_by_args(
                flt=lambda p, ipr: rule_set == {p['FromPort'], p['ToPort'], p['IpProtocol']}
        ):
            with helper.catch(ValueError):
                desc = ip_range.get("Description", None)
                desc = desc[desc.startswith(desc_prefix) and len(desc_prefix):] if desc is not None else desc
                expired_time = parser.parse(desc)
            if expired_time is not None and now >= expired_time.timestamp():
                revoke_ips.append(ip_range)

        ip_permissions = self.__populate_ip_permissions_args(ip_ranges=revoke_ips)
        response = revoke_fn(ip_permissions)  # self.group.revoke_ingress(args)

        status_code = response['ResponseMetadata']['HTTPStatusCode']
        return status_code < 400

    def clear_expired_ips_ingress(self):
        return self.__clear(lambda args: self.group.revoke_ingress(**args))

    def clear_expired_ips_egress(self):
        raise helper.OperationNotSupportedError(f"Clear Egress IPs not supported atm")
