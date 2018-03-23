import time
from datetime import datetime, timedelta

from dateutil import parser

import args
import helper

ip_ranges_desc_prefix = 'expired at '


class SecGroup:

    def __init__(self, **kwargs):
        self.rules = [SecGroupRule(rule) for rule in kwargs.get('rules', [])]
        self.aws_client = kwargs.get('aws_client', None)
        self.aws_group_dict = kwargs.get('aws_group_dict', {})

        self.__aws_rule = None

    @property
    def aws_group_id(self):
        return self.aws_group_dict.get('GroupId')

    @property
    def aws_rules(self):
        if not self.__aws_rule:
            ip_permissions = self.aws_group_dict.get('IpPermissions', [])
            self.__aws_rule = list(
                map(lambda fr: SecGroupRule(
                    type='ingress',  # TODO support type 'egress' also
                    from_port=int(fr['FromPort']),
                    to_port=int(fr['ToPort']),
                    protocol=fr['IpProtocol'],
                    ip_ranges=fr['IpRanges']
                ), filter(lambda ipp: self.by_ip_permission(ipp), ip_permissions))
            )
        return self.__aws_rule

    @classmethod
    def by_ip_permission(cls, ipp):
        ip_ranges = ipp.get('IpRanges', [])
        return next(filter(lambda ip_range: (
                (ip_range.get('CidrIp', '') == args.arguments.cidr_ip) or
                (ip_range.get('Description', '').startswith(ip_ranges_desc_prefix))
        ), ip_ranges))

    @property
    def ingress_rules(self):
        return list(filter(lambda r: r.is_ingress(), self.rules))

    def __get_aws_ip_permissions(self, **kwargs):  # aws ip permissions generator
        expire = kwargs.get('expire', None)

        ip_ranges = kwargs.get('ip_ranges', [])
        if args.arguments.cidr_ip is not None:
            ip_ranges.append(
                {'CidrIp': args.arguments.cidr_ip} if expire is None
                else {
                    'CidrIp': args.arguments.cidr_ip,
                    'Description': ip_ranges_desc_prefix + f'{expire.isoformat()}{time.strftime("%z")}'
                }
            )

        rules = kwargs.get('rules', self.rules)
        ip_permissions = [{
            'IpRanges': ip_ranges if ip_ranges else rule.ip_ranges,
            'FromPort': int(rule.from_port),
            'ToPort': int(rule.to_port),
            'IpProtocol': rule.protocol
        } for rule in rules]

        return {'GroupId': self.aws_group_id, 'IpPermissions': ip_permissions} if ip_permissions else None

    def authorize(self):
        now = datetime.now()
        expire = now + timedelta(days=0, seconds=args.arguments.time_to_expire)
        return self.__retry(
            fn_retries=[
                lambda _, ips: self.aws_client.authorize_security_group_ingress(**ips),
                lambda _, ips: self.aws_client.update_security_group_rule_descriptions_ingress(**ips)
            ],
            expire=expire,
            rules=self.ingress_rules
        )

    def __retry(self, **kwargs):
        fn_retries = kwargs.get('fn_retries')
        error, ips = None, self.__get_aws_ip_permissions(**kwargs)
        for fn_retry in fn_retries:
            error = helper.get_catch(
                fn=lambda: fn_retry(error, ips),
                ignore_error=False,
                ignore_result=True
            ) if ips else None
            if not error: break

        if not error: return

        # we have an error then retry one-by-one
        rules, retry_once = kwargs.get('rules', []), kwargs.get('retry_once', True)
        if len(rules) == 1:
            rules[0].error = error
        elif retry_once:
            for rule in rules:
                kwargs['retry_once'], kwargs['rules'] = False, [rule]
                self.__retry(**kwargs)
        else:
            for rule in rules: rule.error = error

    @property
    def error_rules(self):
        return list(filter(lambda r: r.error, self.rules))

    def revoke(self, revoke_rules=None):
        return self.__retry(
            fn_retries=[lambda _, ips: self.aws_client.revoke_security_group_ingress(**ips)],
            rules=revoke_rules if revoke_rules else self.ingress_rules
        )

    def clear(self):
        now = datetime.now()

        revoke_rules = []
        for aws_rule in self.aws_rules:
            for ip in aws_rule.ip_ranges:
                desc = ip.get('Description', '')
                expired_time = parser.parse(
                    desc[desc.startswith(ip_ranges_desc_prefix) and len(ip_ranges_desc_prefix):]
                ) if not desc else now
                if now.timestamp() >= expired_time.timestamp(): revoke_rules.append(aws_rule)

        return self.revoke(revoke_rules=revoke_rules) if revoke_rules else None


class SecGroupRule():

    def __init__(self, iterable=(), **kwargs):
        self.__dict__.update(iterable, **kwargs)
        self.error = None

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            for p in ['type', 'from_port', 'to_port', 'protocol']:
                vp = int(getattr(self, p)) if p.endswith('port') else getattr(self, p)
                op = int(getattr(other, p)) if p.endswith('port') else getattr(other, p)
                if vp != op: return False
            return True
        return False

    def is_ingress(self):
        return getattr(self, 'type') == 'ingress'

    def is_egress(self):
        return getattr(self, 'type') == 'egress'
