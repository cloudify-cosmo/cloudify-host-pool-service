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
import os
import logging
from subprocess import Popen, PIPE, call
from shutil import rmtree

from fabric2 import task
RUN_WITH = 'source /home/centos/host_pool_service/bin/activate &&'

from cloudify import ctx
from cloudify.exceptions import NonRecoverableError

BASE_DIR = ctx.instance.runtime_properties.get('working_directory')
SVC_NAME = 'cloudify-hostpool'
INIT_PATH = '/etc/init.d/{0}'.format(SVC_NAME)


def cmd_exists(cmd, logger, connection):
    '''Test to see if a command exists on the system'''
    logger.debug('Checking if command "{0}" exists'.format(cmd))
    return connection.run(RUN_WITH + 'type {0}'.format(cmd),
                          warn=True).return_code
    # retval = call("type " + cmd, shell=True, stdout=PIPE, stderr=PIPE) == 0
    # logger.debug('Command "{0}" {1} found'
    #              .format(cmd, 'was' if retval else 'was not'))
    # return retval


def uninstall_service(logger):
    '''Installs the service into /etc/init.d/'''
    logger.debug('(sudo) Deleting init script "{0}"'.format(INIT_PATH))
    # code = run(RUN_WITH + 'sudo rm {0}'.format(INIT_PATH))
    # if code:
    #     raise NonRecoverableError('Failed service stop.')
    # proc = Popen(['sudo', 'rm', INIT_PATH], stderr=PIPE)
    # err = proc.communicate()
    # logger.debug('Operation returned code "{0}"'.format(proc.returncode))
    # if proc.returncode:
    #     logger.error('Error moving init script to '
    #                  '/etc/init.d/: {0}'.format(err))


def remove_service_from_boot(logger, connection):
    '''Disables the service from starting on system boot'''
    # Disable service from boot
    logger.info('(sudo) Disabling the Host-Pool service from '
                'starting on boot')

    # Red Hat
    if cmd_exists('chkconfig', logger, connection):
        try:
            connection.run(RUN_WITH + 'sudo chkconfig --del {0}'.format(SVC_NAME))
        except:
            pass
        # proc = Popen(['sudo', 'chkconfig', '--del', SVC_NAME],
        #              stderr=PIPE)
    # Debian
    elif cmd_exists('update-rc.d', logger, connection):
        code = connection.run(RUN_WITH + 'sudo update-rc.d {0} remove'.format(SVC_NAME))
        #
        # proc = Popen(['sudo', 'update-rc.d', SVC_NAME, 'remove'],
        #              stderr=PIPE)
    # Unknown
    else:
        logger.error('Neither chkconfig or update-rc.d was found')
        code = True

    # if code:
    #     raise NonRecoverableError('Failed chkconfig.')

    # if proc:
    #     err = proc.communicate()
    #     logger.debug('Command returned code "{0}"'.format(proc.returncode))
    #     if proc.returncode:
    #         logger.error('Error disabling Host-Pool service '
    #                      'on boot: {0}'.format(err))


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

    os.system('source {0}/bin/activate'.format(
        ctx.instance.runtime_properties['virtualenv']))

    logger = get_hostpool_logger('delete',
                                 debug=ctx.node.properties.get('debug'))

    if ctx.node.properties.get('run_as_daemon'):
        # Disable the service from starting on boot
        remove_service_from_boot(logger, connection)
        # Delete the actual service sysv init script
        uninstall_service(logger)
    # Delete working directory
    logger.info('Deleting directory "{0}"'.format(BASE_DIR))
    # run('rm {0}'.format(ctx.instance.runtime_properties['virtualenv']))
    # rmtree(BASE_DIR, ignore_errors=True)
    # os.removedirs()


# main()
