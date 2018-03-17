import time
from datetime import datetime, timedelta

import boto3
from dateutil import parser
import json

import args
import helper
from itertools import groupby

ip_ranges_desc_prefix = 'expired at '


class DynaSecGroups:

    def __init__(self):  # proxy event
        security_groups = args.arguments.security_groups
        group_ids = list(map(lambda g: g['group_id'], security_groups))
        region_rules = groupby(args.arguments.security_groups, lambda r: r['region_name'])

        self.sec_groups = []
        for region_name, rules in region_rules:
            ec2 = boto3.resource('ec2', region_name=region_name)
            # TODO support pagination in search func
            result_set = ec2.meta.client.describe_security_groups(Filters=[{'Name': 'group-id', 'Values': group_ids}])
            if len(result_set) > 0:
                self.sec_groups += [SecGroup(
                    aws_client=ec2.meta.client,
                    aws_group_dict=aws_group_dict,
                    rules=rules
                ) for aws_group_dict in result_set['SecurityGroups']]

    def __process(self, fn_process):
        # failure_groups = {}
        for sec_group in self.sec_groups:
            # failure_rules = fn_process(sec_group)
            helper.get_catch(fn=lambda: fn_process(sec_group), ignore_error=False)
            # failure_rules = helper.get_catch(fn=lambda: fn_process(sec_group), ignore_error=False)
            # if failure_rules:
            #     failure_groups[sec_group.group_id] = failure_groups.get(sec_group.group_id, []) + failure_rules
        # return failure_groups

    def authorize(self):
        return self.__process(lambda sg: sg.authorize())

    def revoke(self):
        return self.__process(lambda sg: sg.revoke())

    def clear(self):
        return self.__process(lambda sg: sg.clear())


class SecGroup:

    def __init__(self, **kwargs):
        self.__error = None

        self.rules = [SecGroupRule(rule) for rule in kwargs.get('rules', [])]
        self.aws_client = kwargs.get('aws_client', None)

        aws_group_dict = kwargs.get('aws_group_dict', {})
        self.aws_group_id = aws_group_dict.get('GroupId')

        ip_permissions = aws_group_dict['IpPermissions']
        self.aws_rules = list(
            map(lambda fr: SecGroupRule(
                type='ingress',  # TODO support type 'egress' also
                from_port=int(fr['FromPort']),
                to_port=int(fr['ToPort']),
                protocol=fr['IpProtocol'],
                ip_ranges=fr['IpRanges']
            ), filter(lambda ipp: self.by_ip_permission(ipp), ip_permissions))
        )

    @classmethod
    def by_ip_permission(cls, ipp):
        ip_ranges = ipp.get('IpRanges', [])
        return next(filter(lambda ip_range: (
                (ip_range.get('CidrIp', '') == args.arguments.cidr_ip) or
                (ip_range.get('Description', '').startswith(ip_ranges_desc_prefix))
        ), ip_ranges))

    def get_error_rules(self):
        if self.__error:
            return self.rules
        else:
            return list(filter(lambda r: r.error, self.rules))

    # def __init__(self, group_id, rules, region_name=None):
    #     self.cidr_ip = args.arguments.cidr_ip
    #     self.time_to_expire = args.arguments.time_to_expire
    #     self.rules = [SecGroupRule(rule) for rule in rules]
    #     self.group_id = group_id
    #     self.region_name = region_name
    #
    #     # self.__error = None
    #
    #     error = helper.get_catch(lambda: self.__init_aws(), ignore_error=False)
    #     if error: self.__error_init_aws = error

    # def has_error(self):
    #     return self.__error is not None

    # def __init_aws(self):
    #     ec2 = boto3.resource('ec2', region_name=self.region_name)
    #     group = ec2.SecurityGroup(self.group_id)
    #     self.aws_group = group
    #     self.aws_client = self.aws_group.meta.client
    #     self.aws_region_name = self.aws_client.meta.region_name

    # def process_error(self, error, *args, **kwargs):
    #     return [self.__to_failure_error(errors=error, rules=self.rules)]

    # @property
    # def aws_rules(self):
    #     self.aws_group.load()
    #
    #     # def by_rule(p_rule):
    #     #     if self.cidr_ip:
    #     #         return p_rule['CidrIp'] == self.cidr_ip
    #     #     return p_rule.get('Description', '').startswith(ip_ranges_desc_prefix)

    #     # permissions = list(filter(
    #     #     lambda p: next(filter(lambda r: by_rule(r), p['IpRanges'])),
    #     #     self.aws_group.ip_permissions
    #     # ))

    #     aws_rules = []
    #     for p in permissions:
    #         aws_rules.append(SecGroupRule(
    #             type='ingress',  # TODO support type 'egress' also
    #             from_port=int(p['FromPort']),
    #             to_port=int(p['ToPort']),
    #             protocol=p['IpProtocol'],
    #             ip_ranges=list(filter(lambda r: by_rule(r), p['IpRanges']))
    #         ))
    #     return aws_rules

    # @staticmethod
    # def __to_failure_error(errors, rules):
    #     if not isinstance(errors, (list, tuple)): errors = [errors]
    #     if not isinstance(rules, (list, tuple)): rules = [rules]
    #     return {
    #         'errors': list(map(lambda er: str(er), errors)),
    #         'rules': list(map(lambda r: str(r), rules))
    #     }

    # @property
    # def existing_ingress_rules(self):
    #     return list(filter(lambda r: next(filter(lambda ar: r.is_ingress() and r == ar, self.aws_rules)), self.rules))

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

    # @helper.return_if(has_attr='error_init_aws', error_handler='process_error')
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

    def __retry(self, fn_retries=(), **kwargs):
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
        if len(rules) in [0, 1]:
            rules[0].error = error
        elif retry_once:
            for rule in rules:
                kwargs['rules'] = [rule]
                self.__retry(fn_retries=fn_retries, retry_once=False, **kwargs)
        else: self.__error = error

        # if not retry_once:
        #     if len(rules) == 1: rules[0].error = error
        #     else: self.__error = error
        #     return
        #
        # for rule in rules:
        #     kwargs['rules'] = [rule]
        #     self.__retry(fn_retries=fn_retries, retry_once=False, **kwargs)

        # for rule in rules:  # retry one by one rule
        #     ips = self.__get_aws_ip_permissions(rules=[rule])
        #     if not ips: continue
        #     error = None
        #     for fn_retry in fn_retries:
        #         error = helper.get_catch(
        #             fn=lambda: fn_retry(error, ips),
        #             ignore_error=False,
        #             ignore_result=True
        #         )
        #         if not error: break
        #
        #     if error: rule.error = error

    # @helper.return_if(has_attr='error_init_aws')
    def revoke(self, revoke_rules=None):
        return self.__retry(
            fn_retries=[
                lambda _, ips: self.aws_group.revoke_ingress(**ips),
                lambda _, ips: self.aws_group.revoke_ingress(**ips)
            ],
            rules=revoke_rules if revoke_rules else self.ingress_rules
        )

    # @helper.return_if(has_attr='error_init_aws')
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
                vp = int(getattr(self, p)) if p.endswith('port') else getattr(self, p)
                op = int(getattr(other, p)) if p.endswith('port') else getattr(other, p)
                if vp != op: return False
            return True
        return False

    def __hash__(self):
        return str(self).__hash__()

    def __str__(self):
        return json.dumps(self)

    @property
    def description(self):
        return self.get('Description', '')

    def is_ingress(self):
        return self.type == 'ingress'

    def is_egress(self):
        return self.type == 'egress'
