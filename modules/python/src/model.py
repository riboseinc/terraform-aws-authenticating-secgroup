import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import time
import json
import helper
from dateutil import parser
from abc import ABC, abstractmethod
import args

expired_at = 'expired at {}'


class DynaSecGroups:

    def __init__(self):  # proxy event
        security_groups = args.arguments.security_groups
        self.sec_groups = []
        for region_name in args.arguments.region_names:
            self.sec_groups += [
                SecGroup(group_id=group_id, rules=security_groups[group_id], region_name=region_name)
                for group_id in security_groups.keys()
            ]

    def __process(self, fn_process):
        fail_groups = {}
        for sec_group in self.sec_groups:
            failed_rules = fn_process(sec_group)
            if failed_rules:
                fail_groups[sec_group.aws_group.group_id] = failed_rules
        return fail_groups

    def authorize(self):
        return self.__process(lambda sg: sg.authorize())

    def revoke(self):
        return self.__process(lambda sg: sg.revoke())


class SecGroup:

    def __init__(self, group_id, rules, region_name=None):
        # ec2 = boto3.resource('ec2')
        ec2 = boto3.resource('ec2', region_name=region_name)  # 'us-west-2') #TODO setup region here
        group = ec2.SecurityGroup(group_id)
        group.load()

        self.cidr_ip = args.arguments.cidr_ip
        self.time_to_expire = args.arguments.time_to_expire

        self.rules = [SecGroupRule(rule) for rule in rules]

        self.aws_group = group
        self.aws_rules = []

        permissions = list(filter(
            lambda p: next(filter(lambda r: r['CidrIp'] == self.cidr_ip, p['IpRanges'])),
            self.aws_group.ip_permissions
        ))
        for p in permissions:
            self.aws_rules.append(SecGroupRule(
                type='ingress',
                from_port=p['FromPort'],
                to_port=p['ToPort'],
                protocol=p['IpProtocol'],
                description=next(filter(lambda r: r['CidrIp'] == self.cidr_ip, p['IpRanges']))['Description']
            ))

        self.aws_client = self.aws_group.meta.client

    def __get_awargs_generator(self, **kwargs):
        expire = kwargs.get('expire', None)

        ip_ranges = kwargs.get('ip_ranges', [])
        if self.cidr_ip is not None:
            ip_ranges.append(
                {'CidrIp': self.cidr_ip} if expire is None
                else {
                    'CidrIp': self.cidr_ip,
                    'Description': expired_at.format(f'{expire.isoformat()}{time.strftime("%z")}')
                }
            )

        rules = kwargs.get('rules', self.rules)
        for rule in rules:
            yield rule, {
                'GroupId': self.aws_group.group_id,
                'IpPermissions': [{
                    'IpRanges': ip_ranges,
                    'FromPort': rule.from_port,
                    'ToPort': rule.to_port,
                    'IpProtocol': rule.protocol
                }]
            }

    def authorize(self):
        now = datetime.now()
        expire = now + timedelta(0, self.time_to_expire)

        return self.__send_to_aws(
            fn_send_ingress=lambda awargs: (
                self.aws_group.authorize_ingress(**awargs)
            ),
            fn_duplicate_ingress=lambda awargs: (
                self.aws_client.update_security_group_rule_descriptions_ingress(**awargs)
            ),
            expire=expire
        )

    def __send_to_aws(self, fn_send_ingress, fn_duplicate_ingress=None, **kwargs):
        failed_rules = []
        awargs_generator = self.__get_awargs_generator(**kwargs)
        for rule, awargs in awargs_generator:
            try:
                fn_send_ingress(awargs) if rule.is_ingress() else None
            except Exception as error:
                if isinstance(error, ClientError):
                    error_code = error.response['Error']['Code']
                    if error_code == 'InvalidPermission.Duplicate':
                        fn_duplicate_ingress(awargs) if fn_duplicate_ingress and rule.is_ingress() else None
                failed_rules.append((error, rule))
        return failed_rules

    def revoke(self):
        rules = list(filter(lambda aws_rule: next(filter(lambda rule: rule == aws_rule, self.rules)), self.aws_rules))
        return self.__send_to_aws(fn_send_ingress=lambda awargs: self.aws_group.revoke_ingress(**awargs), rules=rules)


class SecGroupRule(dict):

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, name, value):
        self[name] = value

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            for p in ['type', 'from_port', 'to_port', 'protocol']:
                if getattr(self, p) != getattr(other, p):
                    return False
            return True
        return False

    def is_ingress(self):
        return self.type == 'ingress'

    def is_egress(self):
        return self.type == 'egress'
