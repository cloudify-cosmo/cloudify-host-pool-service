# #######
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

'''
    lifecycle.Configure
    ~~~~~~~~~~~~~~~~~~~
    Configures the Cloudify Host-Pool Service
'''

import os
import yaml
import logging
from tempfile import mkstemp

from fabric2 import task
RUN_WITH = 'source /home/centos/host_pool_service/bin/activate &&'

from cloudify import ctx
from cloudify.exceptions import NonRecoverableError

BASE_DIR = ctx.instance.runtime_properties.get('working_directory')
POOL_CFG_PATH = os.path.join(BASE_DIR, 'pool.yaml')


def get_key_content(key_file, logger, connection):
    '''Downloads a key and returns the key contents'''
    tfd, target_path = mkstemp()
    os.close(tfd)
    logger.debug('Downloading key file "{0}" to path "{1}"'
                 .format(key_file, target_path))
    local_key_file = ctx.download_resource(key_file)
    connection.put(local_key_file, target_path)
    keycontent = None
    with open(target_path, 'r') as f_key:
        keycontent = f_key.read()
        logger.debug('Key file "{0}" contains: {1}'
                     .format(key_file, keycontent))
    os.remove(target_path)
    return keycontent


def set_host_key_content(cfg, logger, connection):
    '''Replaces host key file string with key content

    :param dict cfg: Host-Pool configuration data
    :returns: Updated configuration data
    '''
    # Get the default key (if specified)
    logger.debug('Checking for a default key file')
    defaults = cfg.get('default', {})
    default_key = defaults.get('credentials', {}).get('key')
    default_key_file = defaults.get('credentials', {}).get('key_file')
    # "key" has priority over "key_file"
    if not default_key and default_key_file:
        # Default key file was specified, let's convert and use
        logger.debug('Default key file: "{0}"'.format(default_key_file))
        cfg['default']['credentials']['key'] = \
            get_key_content(default_key_file, logger, connection)
        del cfg['default']['credentials']['key_file']

    # Get the host keys
    for host in cfg.get('hosts'):
        logger.debug('Checking key file for host "{0}"'
                     .format(host.get('name')))
        host_key = host.get('credentials', {}).get('key')
        host_key_file = host.get('credentials', {}).get('key_file')
        # "key" has priority over "key_file"
        if not host_key and host_key_file:
            # Default key file was specified, let's convert and use
            logger.debug('Host key file: "{0}"'.format(host_key_file))
            host['credentials']['key'] = \
                get_key_content(host_key_file, logger, connection)
            del host['credentials']['key_file']
    return cfg


def get_hostpool_logger(mod, debug=False,
                        log_file=None, parent_logger=None):
    '''Configures a host-pool deployment logger'''
    # Preference parent_logger, fallback to ctx.logger
    if not parent_logger:
        if ctx and ctx.logger:
            parent_logger = ctx.logger

    # If neither logger was found, error
    if not parent_logger:
        raise NonRecoverableError(
            'get_hostpool_logger requires either a Cloudify Context '
            'or parent_logger specified')

    # Get a child logger
    logger = parent_logger.getChild(mod)

    if debug:
        logger.setLevel(logging.DEBUG)

        # Preference log_path, fallback working_directory/debug.log
        if not log_file and ctx:
            log_file = os.path.join(
                ctx.instance.runtime_properties.get('working_directory'),
                'debug.log')

        if log_file:
            # Make sure the debug log file exists
            if not os.path.exists(log_file):
                # Create the directory path if needed
                if not os.path.isdir(os.path.dirname(log_file)):
                    os.makedirs(os.path.dirname(log_file))
                # Create the file & update timestamp
                with open(log_file, 'a'):
                    os.utime(log_file, None)

            # Create our log handler for the debug file
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            logger.addHandler(file_handler)

    return logger


@task
def main(connection):
    '''Entry point'''

    logger = get_hostpool_logger('configure',
                                 debug=ctx.node.properties.get('debug'))

    if not ctx.node.properties.get('pool'):
        logger.info('Configuration file for the Host-Pool service '
                    'was not specified. Continuing without seed hosts')
        ctx.instance.runtime_properties['seed_hosts'] = None
        return

    logger.debug('Downloading host-pool configuration file "{0}" to "{1}"'
                 .format(ctx.node.properties['pool'], POOL_CFG_PATH))
    local_file = ctx.download_resource(ctx.node.properties['pool'],
                                       target_path=POOL_CFG_PATH)
    connection.put(local_file, POOL_CFG_PATH)

    # if not os.path.exists(POOL_CFG_PATH):
    #     raise NonRecoverableError('Configuration file for the Host-Pool '
    #                               'service could not be downloaded')

    # Load our configuration data
    with open(local_file) as f_cfg:
        cfg = None
        logger.info('Loading Host-Pool seed hosts')
        try:
            cfg = yaml.load(f_cfg)
        except yaml.YAMLError:
            raise NonRecoverableError('Configuration file for the Host-Pool '
                                      'service is not valid YAML')
        logger.info('Converting host key files from blueprint')
        seed_config = set_host_key_content(cfg, logger, connection)
        ctx.instance.runtime_properties['seed_config'] = seed_config

# main()
