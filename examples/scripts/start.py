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
    lifecycle.Start
    ~~~~~~~~~~~~~~~
    Downloads and starts the Cloudify Host-Pool Service
'''

# import pkgutil
import os
import logging
from time import sleep
from string import Template
import tempfile
from subprocess import Popen, PIPE, call
import requests

from fabric.api import run, put, sudo
RUN_WITH = 'source /home/centos/host_pool_service/bin/activate &&'

from cloudify import ctx
from cloudify.exceptions import NonRecoverableError, RecoverableError
# from cloudify_hostpool.logger import get_hostpool_logger

os.environ['VIRTUALENV'] = ctx.instance.runtime_properties['virtualenv']
BASE_DIR = ctx.instance.runtime_properties.get('working_directory')
VIRT_DIR = os.environ.get('VIRTUALENV') or os.environ.get('VIRTUAL_ENV')
SVC_DEBUG = ctx.node.properties.get('gunicorn_debug')
CONFIG_PATH = ctx.instance.runtime_properties.get('config_path')
HOST = ctx.node.properties.get('host')
PORT = ctx.node.properties.get('port')
SCHEME = 'http'
ENDPOINT = '{0}://{1}:{2}'.format(SCHEME, HOST, PORT)
SVC_NAME = 'cloudify-hostpool'
INIT_PATH = '/etc/init.d/{0}'.format(SVC_NAME)


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


def cmd_exists(cmd, logger):
    '''Test to see if a command exists on the system'''
    logger.debug('Checking if command "{0}" exists'.format(cmd))
    return run(RUN_WITH + 'type {0}'.format(cmd))
    # retval = call("type " + cmd, shell=True, stdout=PIPE, stderr=PIPE) == 0
    # logger.debug('Command "{0}" {1} found'
    #              .format(cmd, 'was' if retval else 'was not'))
    # return retval


def download_service(logger):
    '''Downloads the service file and pre-processes'''
    # Grab the init script from the package
    logger.info('Downloading Host-Pool service init script')
    # init_data = pkgutil.get_data('cloudify_hostpool',
    #                              'resources/service_init.sh')
    # if not init_data:
    #     raise NonRecoverableError('Could not download Host-Pool service '
    #                               'init script from cloudify_hostpool:'
    #                               'resources/service_init.sh')
    #
    # # Pre-process the script (replace defaults)
    # logger.debug('Replacing default values in init script')
    # tmpl = Template(init_data)
    # init_data = tmpl.safe_substitute({
    #     'TMPL_BASE_DIR': BASE_DIR,
    #     'TMPL_VIRT_DIR': VIRT_DIR,
    #     'TMPL_SVC_LOG_LEVEL': 'DEBUG' if SVC_DEBUG else 'INFO'
    # })
    # logger.debug('Init script contents: {0}'.format(init_data))
    #
    # # Write the init script data to a temporary file
    # logger.debug('Creating temporary init script file')
    # (temp_fd, temp_name) = tempfile.mkstemp()
    # logger.debug('Temporary file created: {0}'.format(temp_name))
    # os.write(temp_fd, init_data)
    # os.close(temp_fd)
    variables = {
        'TMPL_BASE_DIR': BASE_DIR,
        'TMPL_VIRT_DIR': VIRT_DIR,
        'TMPL_SVC_LOG_LEVEL': 'DEBUG' if SVC_DEBUG else 'INFO'
    }
    temp_name = ctx.download_resource_and_render(
        'resources/service_init.sh',
        template_variables=variables
    )
    put(temp_name, '/home/centos/temp_service_file')
    return '/home/centos/temp_service_file'


def set_service_permissions(svc, logger):
    '''Set the correct access, owner, and group for the service'''
    # Set init script as executable
    logger.debug('Setting init script as executable')
    # os.chmod(svc, os.stat(svc).st_mode | 0o111)
    # logger.debug('Init script permissions: {0}'
    #              .format(oct(os.stat(svc).st_mode)))
    run('chmod 775 {0}'.format(svc))

    # Set init script owner to root
    logger.debug('(sudo) Setting owner of "{0}" to "root:root"'
                 .format(svc))
    code = run(RUN_WITH + 'sudo chown root:root {0}'.format(svc))
    if code:
        raise NonRecoverableError('Failed chown.')
    # proc = Popen(['sudo', 'chown', 'root:root', svc], stderr=PIPE)
    # err = proc.communicate()
    # if proc.returncode:
    #     raise NonRecoverableError('Error setting owner of "{0}": {1}'
    #                               .format(svc, err))


def install_service(svc, logger):
    '''Installs the service into /etc/init.d/'''
    logger.debug('(sudo) Moving "{0}" to "{1}"'.format(svc, INIT_PATH))
    code = run(RUN_WITH + 'sudo mv {0} {1}'.format(svc, INIT_PATH))
    if code:
        raise NonRecoverableError('Failed mv.')
    # proc = Popen(['sudo', 'mv', svc, INIT_PATH], stderr=PIPE)
    # err = proc.communicate()
    # logger.debug('Operation returned code "{0}"'.format(proc.returncode))
    # if proc.returncode:
    #     raise NonRecoverableError('Error moving init script to '
    #                               '/etc/init.d/: {0}'.format(err))


def start_service(logger):
    '''Starts the service'''
    logger.info('(sudo) Starting the Host-Pool service')
    run(RUN_WITH + 'sudo {0} restart'.format(INIT_PATH))
    # if code:
    #     raise NonRecoverableError('Failed service start.')
    # proc = Popen(['sudo', 'service', SVC_NAME, 'start'], stderr=PIPE)
    # err = proc.communicate()
    # logger.debug('Service returned code "{0}"'.format(proc.returncode))
    # if proc.returncode:
    #     raise RecoverableError('Error starting Host-Pool service: {0}'
    #                            .format(err))


def set_service_on_boot(logger):
    '''Sets up the service to start on system boot'''
    # Enable service on boot
    logger.info('(sudo) Enabling the Host-Pool service on boot')

    # Red Hat
    if cmd_exists('chkconfig', logger):
        code = run(RUN_WITH + 'sudo chkconfig --add {0}'.format(SVC_NAME),
                    shell=False)
        # proc = Popen(['sudo', 'chkconfig', '--add', SVC_NAME],
        #              stderr=PIPE)
    # Debian
    elif cmd_exists('update-rc.d', logger):
        code = run(RUN_WITH + 'sudo update-rc.d {0} defaults'.format(SVC_NAME),
                    shell=False)
        # proc = Popen(['sudo', 'update-rc.d', SVC_NAME, 'defaults'],
        #              stderr=PIPE)
    # Unknown
    else:
        raise NonRecoverableError(
            'Neither chkconfig or update-rc.d was found')

    if code:
        raise NonRecoverableError('Failed chkconfig.')

    # if proc:
    #     err = proc.communicate()
    #     logger.debug('Command returned code "{0}"'.format(proc.returncode))
    #     if code:
    #         raise NonRecoverableError('Error enabling Host-Pool service '
    #                                   'on boot: {0}'.format(err))


def test_service_liveness(logger):
    '''Tests if the service is running correctly'''
    max_attempts = 20
    for i in range(max_attempts):
        logger.info('[Attempt {0}/{1}] Liveness detection check'
                    .format(i, max_attempts))
        logger.debug('GET {0}/hosts'.format(ENDPOINT))
        req = None
        try:
            req = requests.get('{0}/hosts'.format(ENDPOINT))
            logger.debug('HTTP status: {0}'.format(req.status_code))
        except requests.exceptions.RequestException as ex:
            logger.warn('Exception raised connecting to service: {0}'
                        .format(ex))

        # Check the HTTP status code
        if req:
            if req.status_code == 200:
                logger.info('Host-Pool service is alive')
                break
            else:
                logger.error('Bad HTTP status returned: {0}'
                             .format(req.status_code))
        else:
            logger.info('Host-Pool service is not ready yet')

        logger.warn('Waiting 2 seconds before retrying')
        sleep(2)


def install_seed_hosts(logger):
    '''Uses the REST service to install hosts set during deployment'''
    seed_config = ctx.instance.runtime_properties.get('seed_config')
    if seed_config:
        logger.info('Installing seed hosts data')
        try:
            logger.debug('POST /hosts: {0}'.format(seed_config))
            req = requests.post('{0}/hosts'.format(ENDPOINT),
                                json=seed_config)
            logger.debug('HTTP status: {0}'.format(req.status_code))
        except requests.exceptions.RequestException as ex:
            raise RecoverableError(ex)


def start_standalone_service(logger):
    '''Starts a standalone service process'''
    logger.info('Starting the Host-Pool service (standalone)')
    svc_cmd = \
        '{0} --workers={1} --pid="{2}" --log-level="{3}" \
        --log-file="{4}" --bind "0.0.0.0:{5}" --daemon "{6}"'.format(
            os.path.join(VIRT_DIR, 'bin/gunicorn'),
            5,
            os.path.join(BASE_DIR, 'cloudify-hostpool.pid'),
            'DEBUG' if SVC_DEBUG else 'INFO',
            os.path.join(BASE_DIR, 'gunicorn.log'),
            PORT,
            'cloudify_hostpool.rest.service:app'
        )
    logger.debug('Executing: {0}'.format(svc_cmd))
    run(RUN_WITH + svc_cmd)
    # svc_pid = Popen(svc_cmd, shell=True).pid
    # logger.debug('Service task spawned with PID "{0}'.format(svc_pid))


def main():
    '''Entry point'''
    logger = get_hostpool_logger('start',
                                 debug=ctx.node.properties.get('debug'))

    # Make sure VIRTUALENV is set
    if not VIRT_DIR:
        raise NonRecoverableError(
            'VIRTUALENV or VIRTUAL_ENV environment variable must be set!')

    if ctx.node.properties.get('run_as_daemon'):
        # Grab the init script from the package
        svc_tmp = download_service(logger)
        # Set the correct service permissions
        set_service_permissions(svc_tmp, logger)
        # Move the init script to /etc/init.d/
        install_service(svc_tmp, logger)
        # Start the service
        start_service(logger)
        # Enable the service to start on boot
        set_service_on_boot(logger)
    else:
        # Start the stand-alone process
        start_standalone_service(logger)
    # Test if the service is alive
    test_service_liveness(logger)
    # Install any seed hosts data into the service
    install_seed_hosts(logger)
    # Set runtime properties
    ctx.instance.runtime_properties['service_name'] = SVC_NAME
    ctx.instance.runtime_properties['endpoint'] = ENDPOINT

# main()
