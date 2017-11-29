import shutil
import glob
import os
import sys

base = './app'
if not os.path.exists(base):
    os.makedirs(base)

sys.path = list(filter(lambda p: not p.endswith('src'), sys.path))
base_app = os.path.dirname(os.path.abspath(__file__)) + "/app"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/app")


def init_params():
    with open(f'{base}/authorize.py', 'r') as file:
        file_data = file.read()

    file_data = file_data \
        .replace('${type}', 'ingress') \
        .replace("event['requestContext']['identity']['sourceIp']", '"54.149.187.177"') \
        .replace("${security_groups}", '["sg-c9c72eb5", "sg-df7a88a3"]')

    with open(f'{base}/authorize.py', 'w') as file:
        file.write(file_data)

    # helper.py
    with open(f'{base}/helper.py', 'r') as file:
        file_data = file.read()

    file_data = file_data \
        .replace('${from_port}', '22') \
        .replace('${to_port}', '22') \
        .replace('${protocol}', 'tcp') \
        .replace('${time_to_expire}', '600')

    with open(f'{base}/helper.py', 'w') as file:
        file.write(file_data)


if __name__ == "__main__":
    for filename in glob.glob(os.path.join('../src', '*.*')):
        shutil.copy(filename, base)

    init_params()

    from app.authorize import handler

    result = handler()
    print(result)
