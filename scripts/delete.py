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
    lifecycle.Delete
    ~~~~~~~~~~~~~~~~
    Deletes the Cloudify Host-Pool Service
'''

from subprocess import Popen, PIPE, call
from shutil import rmtree
from cloudify import ctx
from cloudify_hostpool.logger import get_hostpool_logger

BASE_DIR = ctx.instance.runtime_properties.get('working_directory')
SVC_NAME = 'cloudify-hostpool'
INIT_PATH = '/etc/init.d/{0}'.format(SVC_NAME)


def cmd_exists(cmd, logger):
    '''Test to see if a command exists on the system'''
    logger.debug('Checking if command "{0}" exists'.format(cmd))
    retval = call("type " + cmd, shell=True, stdout=PIPE, stderr=PIPE) == 0
    logger.debug('Command "{0}" {1} found'
                 .format(cmd, 'was' if retval else 'was not'))
    return retval


def uninstall_service(logger):
    '''Installs the service into /etc/init.d/'''
    logger.debug('(sudo) Deleting init script "{0}"'.format(INIT_PATH))
    proc = Popen(['sudo', 'rm', INIT_PATH], stderr=PIPE)
    err = proc.communicate()
    logger.debug('Operation returned code "{0}"'.format(proc.returncode))
    if proc.returncode:
        logger.error('Error moving init script to '
                     '/etc/init.d/: {0}'.format(err))


def remove_service_from_boot(logger):
    '''Disables the service from starting on system boot'''
    # Disable service from boot
    logger.info('(sudo) Disabling the Host-Pool service from '
                'starting on boot')

    # Red Hat
    if cmd_exists('chkconfig', logger):
        proc = Popen(['sudo', 'chkconfig', '--del', SVC_NAME],
                     stderr=PIPE)
    # Debian
    elif cmd_exists('update-rc.d', logger):
        proc = Popen(['sudo', 'update-rc.d', SVC_NAME, 'remove'],
                     stderr=PIPE)
    # Unknown
    else:
        logger.error('Neither chkconfig or update-rc.d was found')

    if proc:
        err = proc.communicate()
        logger.debug('Command returned code "{0}"'.format(proc.returncode))
        if proc.returncode:
            logger.error('Error disabling Host-Pool service '
                         'on boot: {0}'.format(err))


def main():
    '''Entry point'''
    logger = get_hostpool_logger('delete',
                                 debug=ctx.node.properties.get('debug'))
    if ctx.node.properties.get('run_as_daemon'):
        # Disable the service from starting on boot
        remove_service_from_boot(logger)
        # Delete the actual service sysv init script
        uninstall_service(logger)
    # Delete working directory
    logger.info('Deleting directory "{0}"'.format(BASE_DIR))
    rmtree(BASE_DIR, ignore_errors=True)


main()
