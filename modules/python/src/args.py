import json

import helper


class Arguments:

    def __init__(self):
        self.cidr_ip = self.source_ip = None
        self.__region_names = [None]
        self.__event = None
        self.__security_groups = None
        self.__time_to_expire = None

    @property
    def event(self):
        return self.__event

    @event.setter
    def event(self, event):
        try:
            self.__event = event
            self.source_ip = event['requestContext']['identity']['sourceIp']
            self.cidr_ip = f'{self.source_ip}/32'
        except Exception as error:
            print(f"Ignore error {str(error)}")

    @property
    def security_groups(self):
        if self.__security_groups is None:
            self.security_groups = json.loads('''${security_groups}''')
            # self.__security_groups = self.normalize_groups(json.loads('''${security_groups}'''))
        return self.__security_groups

    @security_groups.setter
    def security_groups(self, groups):
        self.__security_groups = self.normalize_groups(groups)

    @staticmethod
    def normalize_groups(groups):
        security_groups = {}
        for group in groups:
            for group_id in group['group_ids']:
                security_group = security_groups.get(group_id, {})
                rules = security_group.get('rules', []) + group['rules']
                security_groups[group_id] = {
                    'rules': rules,
                    'region_name': group['region_name']
                }
        return security_groups

    @property
    def time_to_expire(self):
        if self.__time_to_expire is None:
            self.__time_to_expire = helper.get_catch(fn=lambda: int("${time_to_expire}"), default=600)
        return self.__time_to_expire

    @time_to_expire.setter
    def time_to_expire(self, seconds):
        self.__time_to_expire = int(seconds)


arguments = Arguments()