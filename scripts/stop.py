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

from subprocess import Popen, PIPE
from cloudify import ctx
from cloudify_hostpool.logger import get_hostpool_logger

SVC_NAME = 'cloudify-hostpool'


def stop_service(logger):
    '''Stops the service'''
    logger.info('(sudo) Stopping the Host-Pool service')
    proc = Popen(['sudo', 'service', SVC_NAME, 'stop'], stderr=PIPE)
    err = proc.communicate()
    logger.debug('Service returned code "{0}"'.format(proc.returncode))

    # Warn and continue
    if proc.returncode:
        logger.warn('Could not stop Host-Pool service: {0}'.format(err))


def main():
    '''Entry point'''
    logger = get_hostpool_logger('stop',
                                 debug=ctx.node.properties.get('debug'))
    # Delete working directory
    logger.info('Stopping service "{0}"'.format(SVC_NAME))
    stop_service(logger)

main()
