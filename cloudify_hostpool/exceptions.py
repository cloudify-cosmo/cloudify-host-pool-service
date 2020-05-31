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
    cloudify_hostpool.exceptions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RESTful service exception handling
'''
from ._compat import httplib


class HostPoolHTTPException(Exception):
    '''An error raised by service modules to handle errors in REST API'''
    def __init__(self, status_code):
        self.status_code = status_code
        super(HostPoolHTTPException, self).__init__(self.__str__())

    def get_code(self):
        '''Get the HTTP response code'''
        return self.status_code

    def to_dict(self):
        '''Get the HTTP response object'''
        return {'error': self.__str__()}


class NoHostAvailableException(HostPoolHTTPException):

    """
    Raised when there are no hosts left to be acquired.

    """

    def __init__(self):
        super(NoHostAvailableException, self).__init__(515)

    def __str__(self):
        return 'Cannot acquire host. All hosts are either in use or not ' \
               'responding.'


class HostNotFoundException(HostPoolHTTPException):

    """
    Raised when there is no host with requested id

    """

    def __init__(self, host_id):
        self.host_id = host_id
        super(HostNotFoundException, self).__init__(httplib.NOT_FOUND)

    def __str__(self):
        return 'Cannot find requested host: {0}'.format(self.host_id)


class UnexpectedData(HostPoolHTTPException):

    """
    Raised when there unexpected or unrecognized data sent
    Common case: non-JSON requests to JSON endpoints

    """

    def __init__(self, message):
        self.message = message
        super(UnexpectedData, self).__init__(httplib.BAD_REQUEST)

    def __str__(self):
        return 'Unexpected data received: {0}'.format(self.message)


class ConfigurationError(Exception):

    """
    Raised when there is some error in the configuration.
    """
    def __init__(self, message):
        super(ConfigurationError, self).__init__(message)


class StorageException(Exception):

    """
    Raised when there is some error in database access.
    """
    def __init__(self, message):
        super(StorageException, self).__init__(message)
