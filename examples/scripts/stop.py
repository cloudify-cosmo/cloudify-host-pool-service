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
    lifecycle.Stop
    ~~~~~~~~~~~~~~
    Stops the Cloudify Host-Pool Service
'''

import os
import logging
from signal import SIGINT
from subprocess import Popen, PIPE

from fabric.api import run, put, sudo
RUN_WITH = 'source /home/centos/host_pool_service/bin/activate &&'

from cloudify import ctx
from cloudify.exceptions import NonRecoverableError

BASE_DIR = ctx.instance.runtime_properties.get('working_directory')
SVC_NAME = 'cloudify-hostpool'


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


def stop_service(logger):
    '''Stops the service'''
    logger.info('(sudo) Stopping the {0} service'.format(SVC_NAME))
    run(RUN_WITH + 'sudo /etc/init.d/{0} stop'.format(SVC_NAME))
    # if code:
    #     raise NonRecoverableError('Failed service stop.')
    # proc = Popen(['sudo', 'service', SVC_NAME, 'stop'], stderr=PIPE)
    # err = proc.communicate()
    # logger.debug('Service returned code "{0}"'.format(proc.returncode))
    #
    # # Warn and continue
    # if proc.returncode:
    #     logger.warn('Could not stop Host-Pool service: {0}'.format(err))


def stop_standalone_service(logger):
    '''Starts a standalone service process'''
    logger.info('Killing the {0} service (standalone)'.format(SVC_NAME))
    svc_pid_file = os.path.join(BASE_DIR, 'cloudify-hostpool.pid')
    if os.path.exists(svc_pid_file):
        logger.debug('Using PID file "{0}"'.format(svc_pid_file))
        with open(svc_pid_file, 'r') as f_svc_pid:
            svc_pid = int(f_svc_pid.read())
            logger.debug('PID: "{0}"'.format(svc_pid))
            os.kill(svc_pid, SIGINT)


def main():
    '''Entry point'''
    # os.system('source {0}/bin/activate'.format(
    #     ctx.instance.runtime_properties['virtualenv']))

    logger = get_hostpool_logger('stop',
                                 debug=ctx.node.properties.get('debug'))
    if ctx.node.properties.get('run_as_daemon'):
        # Delete working directory
        stop_service(logger)
    else:
        # Kill service process
        stop_standalone_service(logger)

# main()
