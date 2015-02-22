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

import abc


class Storage(object):

    """
    Interface for storage transactional operations. All of these operations
    will be called by the server when trying to acquire or release a host.

    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_hosts(self, **filters):

        """
        Retrieves hosts in the database that fit the given filters.
        If no filters are supplied, all hosts are returned.

        :param filters: keyword arguments of filters to search by.
        :type filters: dict

        :return A list of hosts.
        :rtype list of `dict`

        """

    @abc.abstractmethod
    def add_host(self, host):

        """
        Add a host to the database.
        hosts are represented as dictionaries with the following keys:

        {
            'public_address': public ip address or hostname (optional),
            'host': internal ip address or hostname,
            'port': port to communicate to,
            'auth': {
                'username': username to connect to the host with,
                'password': password to connect to the host with (optional),
                'keyfile': path to a key file that enables ssh
                           connection to the host (optional)
            },
            reserved: Boolean flag specifying if to treat this host as
                      reserved or available,
            alive: Boolean flag specifying if to treat this host as
                      alive or dead,
            host_id: id of the client using this host. None if this host is
            not in use.
        }

        **Any implementation of this class must persist the keys stated
        above and allow for the modification and querying of each of them**

        :param host: the host to add.
        :type host: dict

        """

    @abc.abstractmethod
    def update_host(self, global_id, new_values, old_values=None):

        """
        Update a host with new values.

        :param global_id: the global id of the host.
        :type global_id: int

        :param new_values: a partial host dictionary containing the host
        keys to update.
        :type new_values: dict

        :param old_values: a partial host dictionary containing the host
        keys to compare with. the update will be performed only if all the
        current values for the keys match the old values given.
        (compareAndSet)
        :type old_values: dict

        :return the most recent host dict
        :rtype `dict`

        """
