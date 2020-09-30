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
    lifecycle.Create
    ~~~~~~~~~~~~~~~~~~~~~~~~~~
    Creates service dependencies
'''

import os

from fabric2 import task

RUN_WITH = 'source /home/centos/host_pool_service/bin/activate &&'

from cloudify import ctx
from cloudify.exceptions import RecoverableError

RUN_WITH = 'source /home/centos/host_pool_service/bin/activate &&'


def install_requirements(connection):
    '''Install required Python packages'''

    with connection.cd("/home/centos"):
        connection.run('curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py')
        connection.run('python get-pip.py')
    connection.sudo('yum install -y python-virtualenv')
    connection.run('virtualenv /home/centos/host_pool_service')
    ctx.instance.runtime_properties['virtualenv'] = \
            '/home/centos/host_pool_service'

    reqs = [
        'gunicorn==19.4.5',
        'pyyaml==3.11',
        'virtualenv',
        ctx.node.properties.get('source')
    ]

    for req in reqs:
        ctx.logger.info('Installing Python package "{0}"'.format(req))
        connection.run(RUN_WITH + 'pip install {0}'.format(req))
        # install(req)


def create_virtualenv():
    venv_name = 'hpsvc'
    venv_path = os.path.join(os.path.expanduser('~'), venv_name)
    os.system('virtualenv {0}'.format(venv_path))
    ctx.instance.runtime_properties['virtualenv'] = venv_path
    os.system('source {0}/bin/activate'.format(venv_name))


@task
def main(connection):
    '''Entry point'''

    # create_virtualenv()
    base_dir = ctx.node.properties.get('working_directory')
    if not base_dir:
        base_dir = os.path.join(os.path.expanduser('~'), 'hostpool')
    ctx.logger.info('UNAME {0}'.format(os.uname()))
    try:
        ctx.logger.info('Creating working directory: "{0}"'.format(base_dir))
        connection.run('mkdir -p {0}'.format(base_dir))
        # if not os.path.isdir(base_dir):
        #     os.makedirs(base_dir)
    except OSError as ex:
        ctx.logger.error('Error making directory "{0}"'.format(base_dir))
        raise RecoverableError(message=ex, retry_after=2)

    ctx.logger.info('Installing required Python packages')
    install_requirements(connection)

    ctx.logger.info('Setting runtime_property "working_directory" to "{0}"'
                    .format(base_dir))
    ctx.instance.runtime_properties['working_directory'] = base_dir


# main()
