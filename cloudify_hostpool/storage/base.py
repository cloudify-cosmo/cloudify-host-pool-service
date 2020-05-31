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
    cloudify_hostpool.storage.base
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Abstract storage interface for the RESTful service
'''

import abc

from six import add_metaclass


@add_metaclass(abc.ABCMeta)
class Storage(object):
    '''
    Interface for storage transactional operations. All of these operations
    will be called by the server when trying to acquire or release a host.
    '''

    @abc.abstractmethod
    def init_data(self):
        '''Initializes the database by clearing all data'''

    @abc.abstractmethod
    def get_host(self, eid):
        '''Retrieve a host in the host pool by object ID.

        Hosts are represented as dictionaries with the following keys:

        {
            'id': Unique database object ID,
            'alive': Boolean specifying if a host is able to be
                     communicated with,
            'allocated': Boolean specifying if a host is currently
                         allocated / reserved by another user or task,
            'platform': {
                'os': String incidating OS base type (windows, linux, etc),
                'version': OS version string as indicated
                           by platform.version(),
                'distro': Linux-specific string identifying the Linux
                          distribution (platform.linux_distribution),
            },
            'endpoints': [{
                'ip': IP address of the endpoint,
                'port': Port of the endpoint,
                'protocol': String specifying what method to use for
                            communicating with the host. Valid options are
                            "winrm-http", "winrm-https", & "ssh",
                'primary': Boolean specifying if this is the primary endpoint,
                'tags': Array of strings for labelling an endpoint,
            }],
            'credentials': {
                'username': Username to connect to the host with,
                'password': Password to connect to the host with (optional),
                'keyfile': Path to a key file that enables ssh
                           connection to the host (optional)
            }
        }

        :param int eid: Host ID of the host to retrieve
        :returns: Host object
        :rtype: dict
        '''

    @abc.abstractmethod
    def get_hosts(self):
        '''Retrieve a list of all hosts is the host pool.

        :returns: A list of all host entries from the database
        :rtype: list
        '''

    @abc.abstractmethod
    def add_hosts(self, hosts):
        '''Adds multiple host entries to the database

        :param list hosts: List of host objects to add to the database
        :returns: List of new host IDs (integers)
        :rtype: list
        '''

    @abc.abstractmethod
    def update_host(self, eid, host):
        '''Updates an existing host in the database

        This will raise a KeyError exception if a non-existent
        host ID is provided.

        :param int eid: Host ID of the host to update
        :returns: Host ID that was updated (or None)
        :rtype: int
        '''

    @abc.abstractmethod
    def remove_host(self, eid):
        '''Removes an existing host from the database

        This will raise a KeyError exception if a non-existent
        host ID is provided.

        :param int eid: Host ID of the host to remove
        :returns: Host ID that was removed (or None)
        :rtype: int
        '''
