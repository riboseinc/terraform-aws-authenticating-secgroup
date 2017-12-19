import os
import sys

base = './app'
if not os.path.exists(base):
    os.makedirs(base)

sys.path = list(filter(lambda p: not p.endswith('src'), sys.path))
base_app = os.path.dirname(os.path.abspath(__file__)) + "/app"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/app")


def init_params():
    r_file = f'{base}/model.py'
    with open(r_file, 'r') as file:
        file_data = file.read()

    file_data = file_data \
        .replace('${type}', 'ingress') \
        .replace("event['requestContext']['identity']['sourceIp']", '"54.149.187.177"') \
        .replace("${security_groups}", '["sg-c9c72eb5", "sg-df7a88a3"]') \
        .replace('${from_port}', '22') \
        .replace('${to_port}', '22') \
        .replace('${protocol}', 'tcp') \
        .replace('${time_to_expire}', '600')

    with open(r_file, 'w') as file:
        file.write(file_data)