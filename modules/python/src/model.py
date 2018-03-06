import time
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError
from dateutil import parser

import args
import helper

expired_at = 'expired at {}'


class DynaSecGroups:

    def __init__(self):  # proxy event
        security_groups = args.arguments.security_groups
        self.sec_groups = [SecGroup(
            group_id=group_id,
            rules=security_groups[group_id]['rules'],
            region_name=security_groups[group_id]['region_name']
        ) for group_id in security_groups.keys()]

    def __process(self, fn_process):
        ok_groups, failure_groups = {}, {}
        for sec_group in self.sec_groups:
            ok, failure = fn_process(sec_group)
            if ok: ok_groups[sec_group.group_id] = ok
            if failure: failure_groups[sec_group.group_id] = failure
        return ok_groups, failure_groups

    def authorize(self):
        return self.__process(lambda sg: sg.authorize())

    def revoke(self):
        return self.__process(lambda sg: sg.revoke())

    def clear(self):
        return self.__process(lambda sg: sg.clear())


class SecGroup:

    def __init__(self, group_id, rules, region_name=None):
        self.cidr_ip = args.arguments.cidr_ip
        self.time_to_expire = args.arguments.time_to_expire
        self.rules = [SecGroupRule(rule) for rule in rules]
        self.group_id = group_id

        try:
            ec2 = boto3.resource('ec2', region_name=region_name)  # 'us-west-2') #TODO setup region here
            group = ec2.SecurityGroup(group_id)
            group.load()

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
            self.aws_region_name = self.aws_client.meta.region_name
        except Exception as error:
            self.error_loading = error

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
                'GroupId': self.group_id,
                'IpPermissions': [{
                    'IpRanges': ip_ranges,
                    'FromPort': int(rule.from_port),
                    'ToPort': int(rule.to_port),
                    'IpProtocol': rule.protocol
                }]
            }

    @helper.return_if(has_attr='error_loading', return_attr='error_loading__send_to_aws')
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

    @property
    def error_loading__send_to_aws(self):
        return [], [{'error': str(self.error_loading), 'rules': self.rules}]

    def __send_to_aws(self, fn_send_ingress, fn_duplicate_ingress=None, **kwargs):
        ok_rules = []
        failure_rules = []
        awargs_generator = self.__get_awargs_generator(**kwargs)

        for rule, awargs in awargs_generator:
            response = helper.get_catch(
                pass_error=False,
                fn=lambda: fn_send_ingress(awargs) if rule.is_ingress() else None
            )

            if isinstance(response, ClientError):
                if response.response['Error']['Code'] == 'InvalidPermission.Duplicate':
                    response = helper.get_catch(
                        pass_error=False,
                        fn=lambda: fn_duplicate_ingress(awargs) if rule.is_ingress() else None
                    )

            if isinstance(response, Exception):
                failure_rules.append({'error': str(response), 'rules': [rule]})
            else:
                ok_rules.append(rule)

        return ok_rules, failure_rules

    @helper.return_if(has_attr='error_loading', return_attr='error_loading__send_to_aws')
    def revoke(self, revoke_rules=None):
        if not revoke_rules:
            revoke_rules = list(filter(
                lambda aws_rule: next(filter(lambda rule: rule == aws_rule, self.rules)),
                self.aws_rules
            ))
        return self.__send_to_aws(
            fn_send_ingress=lambda awargs: self.aws_group.revoke_ingress(**awargs),
            rules=revoke_rules
        )

    @helper.return_if(has_attr='error_loading', return_attr='error_loading__send_to_aws')
    def clear(self):
        now, desc_prefix = datetime.now(), expired_at.format("")
        aws_rules = list(filter(
            lambda aws_rule: next(filter(
                lambda rule: aws_rule.get('description', '').startswith(desc_prefix) and rule == aws_rule,
                self.rules
            )),
            self.aws_rules
        ))

        revoke_rules = []
        for aws_rule in aws_rules:
            desc = aws_rule.description
            expired_time = parser.parse(desc[desc.startswith(desc_prefix) and len(desc_prefix):])
            if now.timestamp() >= expired_time.timestamp(): revoke_rules.append(aws_rule)

        return self.revoke(revoke_rules) if revoke_rules else None, None


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
