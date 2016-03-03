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
from subprocess import Popen, PIPE
from cloudify import ctx
from cloudify.exceptions import RecoverableError


def install_requirements():
    '''Install required Python packages'''
    reqs = [
        'gunicorn==19.4.5',
        'pyyaml==3.11',
        ctx.node.properties.get('source')
    ]

    for req in reqs:
        ctx.logger.info('Installing Python package "{0}"'.format(req))
        proc = Popen(['pip', 'install', req], stderr=PIPE)
        err = proc.communicate()
        if proc.returncode:
            ctx.logger.error('Installing Python package "{0}" failed'
                             .format(req))
            raise RecoverableError(message=err, retry_after=2)


def main():
    '''Entry point'''
    base_dir = ctx.node.properties.get('working_directory')
    if not base_dir:
        base_dir = os.path.join(os.path.expanduser('~'), 'hostpool')

    try:
        ctx.logger.info('Creating working directory: "{0}"'.format(base_dir))
        if not os.path.isdir(base_dir):
            os.makedirs(base_dir)
    except OSError as ex:
        ctx.logger.error('Error making directory "{0}"'.format(base_dir))
        raise RecoverableError(message=ex, retry_after=2)

    ctx.logger.info('Installing required Python packages')
    install_requirements()

    ctx.logger.info('Setting runtime_property "working_directory" to "{0}"'
                    .format(base_dir))
    ctx.instance.runtime_properties['working_directory'] = base_dir


main()
