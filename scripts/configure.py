import yaml
import os
import json

from cloudify import ctx


pool = ctx.node.properties['pool']
work_directory = ctx.instance.runtime_properties['work_directory']
config_path = os.path.join(work_directory, 'config.json')


def _get_keys():
    with open(pool_config_path) as f:
        pool_json = yaml.load(f)
    default_key = pool_json.get('default', {}).get('keyfile')
    keys = set()
    if default_key:
        keys.add(default_key)
    for host in pool_json['hosts']:
        key = host.get('keyfile')
        if key:
            keys.add(key)
    return keys


def download_pool_config():
    _pool_config = os.path.join(work_directory, os.path.basename(pool))
    ctx.download_resource(pool, target_path=_pool_config)
    return _pool_config


def write_host_pool_config_file():
    config_json = {
        'pool': pool_config_path
    }
    with open(config_path, 'w') as f:
        json.dump(config_json, f, indent=2)

pool_config_path = download_pool_config()
key_files = _get_keys()
for key_file in key_files:
    target_path = os.path.join(work_directory, key_file)
    directory = os.path.dirname(target_path)
    os.makedirs(directory)
    ctx.download_resource(key_file, target_path)

write_host_pool_config_file()

ctx.instance.runtime_properties['config_path'] = config_path

