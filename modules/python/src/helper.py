import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import time
import json
from botocore.model import OperationNotFoundError


class DynaSecGroups:
    handle_type = "${type}"

    def __init__(self, event):
        if self.handle_type not in ['ingress', 'egress']:
            raise OperationNotFoundError(f"Not found handler for type {self.handle_type.upper()}")

        cidr_ip = event['requestContext']['identity']['sourceIp'] + '/32'
        security_groups = json.loads('${security_groups}')
        rule = Rule(cidr_ip=cidr_ip)
        self.sec_groups = [SecGroup(group_id=group_id, rule=rule) for group_id in security_groups]

    def __do_ingress_or_egress(self, ingress, egress):
        has_updated = True
        fail_groups = []
        for sec_group in self.sec_groups:
            has_updated = ingress(sec_group) if self.handle_type == 'ingress' else egress(sec_group)
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


class Rule():
    cidr_ip = ""
    from_port = "${from_port}"
    to_port = "${to_port}"
    protocol = "${protocol}"
    time_to_expire = "${time_to_expire}"

    def __init__(self, **kwargs):
        self.cidr_ip = kwargs['cidr_ip']

    def populate_ip_permissions_args(self, group_id, expire=None):
        args = {
            "GroupId": group_id,
            "IpPermissions": [
                {
                    'FromPort': int(self.from_port),
                    'ToPort': int(self.to_port),
                    'IpProtocol': self.protocol,
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


class SecGroup():

    def __init__(self, group_id, rule):
        ec2 = boto3.resource('ec2')
        group = ec2.SecurityGroup(group_id)
        group.load()

        self.group = group
        self.client = self.group.meta.client

        self.rule = rule

    def __authorize(self, fn_authorize, fn_update):
        now = datetime.now()
        expire = now + timedelta(0, int(self.rule.time_to_expire))
        ip_permissions = self.rule.populate_ip_permissions_args(group_id=self.group.group_id, expire=expire)

        try:
            fn_authorize(ip_permissions)
            return True
        except Exception as error:
            if not isinstance(error, ClientError):
                raise error

            error_code = error.response['Error']['Code']
            if error_code == 'InvalidPermission.Duplicate':
                # self.client.update_security_group_rule_descriptions_ingress(**ip_permissions)
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
        rule_set = {int(self.rule.from_port), int(self.rule.to_port), self.rule.cidr_ip, self.rule.protocol}
        for p in permissions:
            for ip_range in p['IpRanges']:
                p_set = {p['IpProtocol'], p['FromPort'], p['ToPort'], ip_range['CidrIp']}
                if rule_set == p_set:
                    return p, ip_range
        return None, None

    def __revoke(self):
        pass

    def revoke_ingress(self):
        permissions = self.group.ip_permissions  # or self.group.ip_permissions_egress
        # cidr_ips = [x for x in map(lambda p: p['IpRanges'], permissions)] # list(map(lambda p: x for x in p['IpRanges'], permissions))
        permission, ip_range = self.__find_permission_by_rule(permissions)
        if permission is None:
            return False

        ip_permissions = self.rule.populate_ip_permissions_args(group_id=self.group.group_id)
        response = self.group.revoke_ingress(**ip_permissions)
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        return status_code < 400

    def revoke_egress(self):
        pass
