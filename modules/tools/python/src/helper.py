import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import time


class Rule():
    cidr_ip = ""
    from_port = "${from_port}"
    to_port = "${to_port}"
    protocol = "${protocol}"
    time_to_expire = "${time_to_expire}"

    def __init__(self, **kwargs):
        self.cidr_ip = kwargs['cidr_ip']

    def populate_ip_permissions_args(self, group_id, expire):
        return {
            "GroupId": group_id,
            "IpPermissions": [
                {
                    'FromPort': int(self.from_port),
                    'ToPort': int(self.to_port),
                    'IpProtocol': self.protocol,
                    'IpRanges': [
                        {
                            'CidrIp': self.cidr_ip,
                            'Description': f'{expire.isoformat()}{time.strftime("%z")}'
                        }
                    ]
                }
            ]
        }


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
        ip_permissions = self.rule.populate_ip_permissions_args(self.group.group_id, expire)

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
