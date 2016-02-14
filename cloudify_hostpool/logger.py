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
    hostpool.logger
    ~~~~~~~~~~~~~~~
    Creates the Cloudify Host-Pool Service logger
'''

import logging
import os
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError


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
