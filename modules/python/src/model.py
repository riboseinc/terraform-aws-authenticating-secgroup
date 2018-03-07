import time
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError
from dateutil import parser
import json

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
        failure_groups = {}
        for sec_group in self.sec_groups:
            # failure_rules = fn_process(sec_group)
            failure_rules = helper.get_catch(fn=lambda: fn_process(sec_group), ignore_error=False)
            if failure_rules:
                failure_groups[sec_group.group_id] = failure_groups.get(sec_group.group_id, []) + failure_rules
        return failure_groups

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
        self.region_name = region_name

        error = helper.get_catch(lambda: self.__init_aws(), ignore_error=False)
        if error: self.error_init_aws = error

    def __init_aws(self):
        ec2 = boto3.resource('ec2', region_name=self.region_name)
        group = ec2.SecurityGroup(self.group_id)
        self.aws_group = group
        self.aws_client = self.aws_group.meta.client
        self.aws_region_name = self.aws_client.meta.region_name

    def process_error(self, error, *args, **kwargs):
        return [self.__to_failure_error(errors=error, rules=self.rules)]

    @property
    def aws_rules(self):
        self.aws_group.load()
        permissions = list(filter(
            lambda p: next(filter(lambda r: r['CidrIp'] == self.cidr_ip, p['IpRanges'])),
            self.aws_group.ip_permissions
        ))

        aws_rules = []
        for p in permissions:
            aws_rules.append(SecGroupRule(
                type='ingress',  # TODO support type 'egress' also
                from_port=p['FromPort'],
                to_port=p['ToPort'],
                protocol=p['IpProtocol'],
                description=next(filter(lambda r: r['CidrIp'] == self.cidr_ip, p['IpRanges']))['Description']
            ))
        return aws_rules

    @staticmethod
    def __to_failure_error(errors, rules):
        if not isinstance(errors, (list, tuple)): errors = [errors]
        if not isinstance(rules, (list, tuple)): rules = [rules]
        return {
            'errors': list(map(lambda er: str(er), errors)),
            'rules': list(map(lambda r: str(r), rules))
        }

    @property
    def existing_ingress_rules(self):
        return list(filter(lambda r: next(filter(lambda ar: r.is_ingress() and r == ar, self.aws_rules)), self.rules))

    @property
    def ingress_rules(self):
        return list(filter(lambda r: r.is_ingress(), self.rules))

    def __get_aws_ip_permissions(self, **kwargs):  # aws ip permissions generator
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
        ip_permissions = [{
            'IpRanges': ip_ranges,
            'FromPort': int(rule.from_port),
            'ToPort': int(rule.to_port),
            'IpProtocol': rule.protocol
        } for rule in rules]

        return {'GroupId': self.group_id, 'IpPermissions': ip_permissions} if ip_permissions else None

    @helper.return_if(has_attr='error_init_aws', error_handler='process_error')
    def authorize(self):
        now = datetime.now()
        expire = now + timedelta(0, self.time_to_expire)
        return self.__retry(
            fn_retries=[
                lambda _, ips: self.aws_group.authorize_ingress(**ips),
                lambda _, ips: self.aws_client.update_security_group_rule_descriptions_ingress(**ips)
            ],
            expire=expire,
            rules=self.ingress_rules
        )

    def __retry(self, fn_retries=(), **kwargs):
        last_error, ips = None, self.__get_aws_ip_permissions(**kwargs)

        for fn_retry in fn_retries:
            last_error = helper.get_catch(
                fn=lambda: fn_retry(last_error, ips),
                ignore_error=False,
                ignore_result=True
            ) if ips else None
            if not last_error: break

        if not last_error: return None
        rules, retry_once = kwargs.get('rules', []), kwargs.get('retry_once', True)
        if not retry_once: return self.__to_failure_error(errors=last_error, rules=rules)

        last_error, failure_rules = None, []
        for rule in rules:  # retry one by one rule
            ips = self.__get_aws_ip_permissions(rules=[rule])
            if not ips: continue

            for fn_retry in fn_retries:
                last_error = helper.get_catch(
                    fn=lambda: fn_retry(last_error, ips),
                    ignore_error=False,
                    ignore_result=True
                )
                if not last_error: break
            if last_error: failure_rules.append(self.__to_failure_error(errors=last_error, rules=rule))
        return failure_rules

    @helper.return_if(has_attr='error_init_aws')
    def revoke(self, revoke_rules=None):
        return self.__retry(
            fn_retries=[
                lambda _, ips: self.aws_group.revoke_ingress(**ips),
                lambda _, ips: self.aws_group.revoke_ingress(**ips)
            ],
            rules=revoke_rules if not revoke_rules else self.ingress_rules
        )

    @helper.return_if(has_attr='error_init_aws')
    def clear(self):
        pass
        # now, desc_prefix = datetime.now(), expired_at.format("")
        # aws_rules = list(filter(
        #     lambda aws_rule: next(filter(
        #         lambda rule: aws_rule.get('description', '').startswith(desc_prefix) and rule == aws_rule,
        #         self.rules
        #     )),
        #     self.aws_rules
        # ))
        #
        # revoke_rules = []
        # for aws_rule in aws_rules:
        #     desc = aws_rule.description
        #     expired_time = parser.parse(desc[desc.startswith(desc_prefix) and len(desc_prefix):])
        #     if now.timestamp() >= expired_time.timestamp(): revoke_rules.append(aws_rule)
        #
        # return self.revoke(revoke_rules=revoke_rules) if revoke_rules else None, None


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

    def __hash__(self):
        return str(self).__hash__()

    def __str__(self):
        return json.dumps(self)

    def is_ingress(self):
        return self.type == 'ingress'

    def is_egress(self):
        return self.type == 'egress'
