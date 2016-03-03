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
from signal import SIGINT
from subprocess import Popen, PIPE
from cloudify import ctx
from cloudify_hostpool.logger import get_hostpool_logger

BASE_DIR = ctx.instance.runtime_properties.get('working_directory')
SVC_NAME = 'cloudify-hostpool'


def stop_service(logger):
    '''Stops the service'''
    logger.info('(sudo) Stopping the {0} service'.format(SVC_NAME))
    proc = Popen(['sudo', 'service', SVC_NAME, 'stop'], stderr=PIPE)
    err = proc.communicate()
    logger.debug('Service returned code "{0}"'.format(proc.returncode))

    # Warn and continue
    if proc.returncode:
        logger.warn('Could not stop Host-Pool service: {0}'.format(err))


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
    logger = get_hostpool_logger('stop',
                                 debug=ctx.node.properties.get('debug'))
    if ctx.node.properties.get('run_as_daemon'):
        # Delete working directory
        stop_service(logger)
    else:
        # Kill service process
        stop_standalone_service(logger)

main()
