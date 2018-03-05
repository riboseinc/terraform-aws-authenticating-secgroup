import shutil
import glob
import os
import json
import sys

import args

with open(f'{os.getcwd()}/security_groups.json', 'r') as file: groups_json = file.read()
args.arguments.security_groups = json.loads(groups_json)
args.arguments.time_to_expire = 600
# args.arguments.region_names = ['us-west-2', 'us-west-1']

with open(f'{os.getcwd()}/event.json', 'r') as file: args = file.read()
event = json.loads(args)
