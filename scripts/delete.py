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

from shutil import rmtree
from cloudify import ctx
from cloudify_hostpool.logger import get_hostpool_logger

BASE_DIR = ctx.instance.runtime_properties.get('working_directory')


def main():
    '''Entry point'''
    logger = get_hostpool_logger('delete',
                                 debug=ctx.node.properties.get('debug'))
    # Delete working directory
    logger.info('Deleting directory "{0}"'.format(BASE_DIR))
    rmtree(BASE_DIR, ignore_errors=True)


main()
