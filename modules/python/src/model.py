import time
from datetime import datetime, timedelta

from dateutil import parser

import args
import helper
import json


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
    def aws_ingress_rules(self):
        if not self.__aws_rule:
            ip_permissions = self.aws_group_dict.get('IpPermissions', [])
            self.__aws_rule = list(
                map(lambda fr: SecGroupRule(
                    type='ingress',  # TODO support type 'egress' also
                    from_port=int(fr['FromPort']),
                    to_port=int(fr['ToPort']),
                    protocol=fr['IpProtocol'],
                    ip_ranges=fr['IpRanges'],
                    origin=fr
                ), ip_permissions)
            )
        return self.__aws_rule

    # @classmethod
    # def by_ip_permission(cls, ipp):
    #     ip_ranges = ipp.get('IpRanges', [])
    #     expired_at_term = args.Arguments.EXPIRED_AT % ""
    #     return next(filter(lambda ip_range: (
    #             (ip_range.get('CidrIp', '') == args.arguments.cidr_ip) or
    #             (ip_range.get('Description', '').startswith(expired_at_term))
    #     ), ip_ranges))

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
                    'Description': args.Arguments.EXPIRED_AT % f'{expire.isoformat()}{time.strftime("%z")}'
                }
            )

        rules = kwargs.get('rules', self.rules)
        ip_permissions = [{
            'IpRanges': ip_ranges if ip_ranges else rule.ip_ranges,
            'FromPort': int(rule.from_port),
            'ToPort': int(rule.to_port),
            'IpProtocol': rule.protocol
        } for rule in rules]  # self.aws_group_dict.get('IpPermissions', []) +

        # TOTO append rules , not replace it

        # {'IpRanges': [{'CidrIp': '171.249.234.216/32', 'Description': 'expired-at-2018-04-17T12:30:30.430763+0700'}],
        #  'FromPort': 55, 'ToPort': 55, 'IpProtocol': 'tcp'}

        # {'FromPort': 55, 'IpProtocol': 'tcp',
        #  'IpRanges': [{'CidrIp': '171.249.234.216/32', 'Description': 'expired-at-2018-04-17T12:30:30.430763+0700'}],
        #  'Ipv6Ranges': [], 'PrefixListIds': [], 'ToPort': 55, 'UserIdGroupPairs': []}

        aws_args = {'GroupId': self.aws_group_id, 'IpPermissions': ip_permissions} if ip_permissions else None
        args.arguments.logger.debug(f"Arguments send to aws: {aws_args}")
        return aws_args

    def authorize(self):
        now = datetime.now()
        expire = now + timedelta(days=0, seconds=args.arguments.time_to_expire)

        rules = self.ingress_rules
        for rule1 in self.ingress_rules:
            for rule2 in self.aws_ingress_rules:
                if not rule1.merge(rule2):
                    rules.append(rule2)

        self.__retry(
            fn_retries=[
                lambda _, aws_args: self.aws_client.authorize_security_group_ingress(**aws_args),
                lambda _, aws_args: self.aws_client.update_security_group_rule_descriptions_ingress(**aws_args)
            ],
            expire=expire,
            rules=set(rules)
        )
        args.arguments.logger.info(f"Group {self.aws_group_id} authorized, error: {self.error_rules}")

    def __retry(self, **kwargs):
        fn_retries = kwargs.get('fn_retries')
        error, ips = None, self.__get_aws_ip_permissions(**kwargs)

        args.arguments.logger.debug(f"Do action for group {self.aws_group_id} all rules in once call")

        for fn_retry in fn_retries:
            error = helper.get_catch(
                fn=lambda: fn_retry(error, ips),
                ignore_error=False,
                ignore_result=True
            ) if ips else None
            if not error: break

        if not error:
            args.arguments.logger.info(f"Group {self.aws_group_id} is done")
            return

        args.arguments.logger.debug(
            f"Error: {str(error)} => try do action for group {self.aws_group_id} one by one rule")

        # we have an error then retry one-by-one
        rules, retry_once = kwargs.get('rules', []), kwargs.get('retry_once', True)
        if len(rules) == 1:
            rules[0].error = str(error)
        elif retry_once:
            for rule in rules:
                kwargs['retry_once'], kwargs['rules'] = False, [rule]
                self.__retry(**kwargs)
            args.arguments.logger.info(f"Group {self.aws_group_id} is done")
        else:
            for rule in rules: rule.error = str(error)

    @property
    def error_rules(self):
        return list(filter(lambda r: r.error, self.rules))

    def revoke(self, revoke_rules=None):
        self.__retry(
            fn_retries=[lambda _, ips: self.aws_client.revoke_security_group_ingress(**ips)],
            rules=revoke_rules if revoke_rules else self.ingress_rules
        )
        args.arguments.logger.info(f"Group {self.aws_group_id} revoked, error: {self.error_rules}")

    def clear(self):
        now = datetime.now()
        expired_term = args.Arguments.EXPIRED_AT % ""

        revoke_rules, aws_rules = [], self.aws_ingress_rules
        args.arguments.logger.debug(f"aws_ingress_rules: {aws_rules}")
        for aws_rule in aws_rules:
            for ip in aws_rule.ip_ranges:
                desc = ip.get('Description', '')
                expired_time = parser.parse(
                    desc[desc.startswith(expired_term) and len(expired_term):]
                ) if not desc else now
                args.arguments.logger.debug(f"ip: {ip} expired_time: {expired_time}")
                if now.timestamp() >= expired_time.timestamp():
                    args.arguments.logger.debug(f"ip: {ip} is added to revoke list")
                    revoke_rules.append(aws_rule)

        args.arguments.logger.debug(f"revoke_rules: {revoke_rules}")
        if revoke_rules:
            self.revoke(revoke_rules=revoke_rules)
        args.arguments.logger.info(f"Group {self.aws_group_id} cleared, error: {self.error_rules}")


class SecGroupRule():

    def __init__(self, iterable=(), **kwargs):
        self.type = None
        self.protocol = None
        self.to_port = None
        self.from_port = None
        self.ip_ranges = []

        self.__dict__.update(iterable, **kwargs)
        self.error = None

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return str(self) == str(other)
        return False

    def __hash__(self) -> int:
        return str(self).__hash__()

    def __str__(self) -> str:
        return json.dumps({
            "from_port": self.from_port,
            "to_port": self.to_port,
            "protocol": self.protocol,
            "type": self.type,
            "ip_ranges": [{
                "CidrIp": ipr["CidrIp"],
                "Description": ipr["Description"]
            } for ipr in self.ip_ranges]
        })

    def has_same_ports(self, other):
        for p in ['type', 'from_port', 'to_port', 'protocol']:
            if str(getattr(self, p, "v2")) != str(getattr(other, p, "v1")):
                return False
        return True

    def merge(self, other):
        if self.has_same_ports(other):
            return False

        other_iprs = []
        for ipr1 in self.ip_ranges:
            for ipr2 in other.ip_ranges:
                if ipr1["CidrIp"] == ipr2["CidrIp"]:
                    ipr1["Description"] = ipr2["Description"]
                else:
                    other_iprs.append(ipr2)
        self.ip_ranges += other_iprs
        return True

    def is_ingress(self):
        return getattr(self, 'type') == 'ingress'

    def is_egress(self):
        return getattr(self, 'type') == 'egress'
