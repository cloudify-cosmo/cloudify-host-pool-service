########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.


class HostPoolHTTPException(Exception):

    """
    An error raised by service modules to handle errors in REST API

    """

    def __init__(self, status_code):
        self.status_code = status_code
        super(HostPoolHTTPException, self).__init__(self.__str__())

    def get_code(self):
        return self.status_code

    def to_dict(self):
        return {'error': self.__str__()}


class NoHostAvailableException(HostPoolHTTPException):

    """
    Raised when there are no hosts left to be acquired.

    """

    def __init__(self):
        super(NoHostAvailableException, self).__init__(515)

    def __str__(self):
        return 'Cannot acquire host. The pool is ' \
               'all hosts are either is use or not responding.'


class HostNotFoundException(HostPoolHTTPException):

    """
    Raised when there is no host with requested id

    """

    def __init__(self, host_id):
        self.host_id = host_id
        super(HostNotFoundException, self).__init__(404)

    def __str__(self):
        return 'Cannot find requested host: {0}'.format(self.host_id)


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
