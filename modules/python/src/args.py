import helper
import logging
import boto3


class Arguments:
    EXPIRED_AT = 'expired-at-%s'

    # TODO add logger method
    def __init__(self):
        self.cidr_ip = self.source_ip = None
        self.security_groups_dict = {}
        self.origin_security_groups = None
        self.api_caller = "SYSTEM"

        self.__region_names = [None]
        self.__event = None
        self.__security_groups = None
        self.__time_to_expire = None
        self.__logger = None

    @property
    def logger(self):
        if not self.__logger:
            self.__logger = logging.getLogger()
            self.__logger.setLevel(helper.get_catch(
                fn=lambda: int(logging.getLevelName("${log_level}")),
                default="INFO",
                ignore_result=False,
                ignore_error=True
            ))
        return self.__logger

    @property
    def event(self):
        return self.__event

    @event.setter
    def event(self, event):
        try:
            self.__event = event

            user_arn = self.__event['requestContext']["identity"]["userArn"]
            if user_arn:
                self.api_caller = user_arn.split("/")[-1]

            self.source_ip = event['requestContext']['identity']['sourceIp']
            self.cidr_ip = f'{self.source_ip}/32'
        except (KeyError, AssertionError, TypeError) as error:
            print(f"Ignore error {str(error)}")

    @property
    def security_groups(self):
        if self.__security_groups is None:
            self.origin_security_groups = helper.json_loads('''${security_groups}''')
            self.security_groups = self.origin_security_groups
        return self.__security_groups

    @security_groups.setter
    def security_groups(self, groups):
        self.logger.debug(f"origin security_groups: {groups}")
        self.__security_groups = self.normalize_groups(groups)

    def normalize_groups(self, groups):
        self.security_groups_dict = {}
        for group in groups:
            for group_id in group['group_ids']:
                security_group = self.security_groups_dict.get(group_id, {})
                rules = security_group.get('rules', []) + group['rules']
                self.security_groups_dict[group_id] = {
                    'rules': rules,
                    'group_id': group_id,
                    'region_name': group['region_name']
                }
        return [rule for _, rule in self.security_groups_dict.items()]

    @property
    def time_to_expire(self):
        if self.__time_to_expire is None:
            self.__time_to_expire = helper.get_catch(fn=lambda: int("${time_to_expire}"), default=600)
        return self.__time_to_expire

    @time_to_expire.setter
    def time_to_expire(self, seconds):
        self.__time_to_expire = int(seconds)

    @property
    def accessible_users(self):
        s3 = boto3.resource('s3')
        bucket = s3.Bucket('${bucket_name}')
        users = []
        for obj in bucket.objects.all():
            user_json_str =  obj.get()['Body'].read().decode('utf-8')
            self.logger.debug(user_json_str)
            users += helper.json_loads(user_json_str)

        return users


arguments = Arguments()
