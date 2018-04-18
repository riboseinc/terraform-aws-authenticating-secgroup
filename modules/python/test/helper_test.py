import shutil
import glob
import os
import json
import sys

# sys.path = list(filter(lambda p: not p.endswith('src'), sys.path))
# base_app = os.path.dirname(os.path.abspath(__file__)) + "../src"
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/src")

import args

with open(f'{os.getcwd()}/security_groups.json', 'r') as file: groups_json = file.read()
args.arguments.security_groups = json.loads(groups_json)
args.arguments.time_to_expire = 120

with open(f'{os.getcwd()}/event.json', 'r') as file: args = file.read()
event = json.loads(args)
