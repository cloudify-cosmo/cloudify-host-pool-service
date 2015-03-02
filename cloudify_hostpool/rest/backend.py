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

import os
import uuid

from cloudify_hostpool.hosts import scan
from cloudify_hostpool.storage import sqlite
from cloudify_hostpool.config import yaml_pool
from cloudify_hostpool import exceptions


_DB_FILE_PATH_ENV = 'CFY_HOST_POOL_DB_FILE'


class RestBackend(object):

    def __init__(self, pool, db_file_name=None):
        if db_file_name is None:
            db_file_name = os.environ.get(_DB_FILE_PATH_ENV)
            if db_file_name is None:
                if pool.endswith('.yaml'):
                    basename = pool.rsplit('.yaml', 1)[0]
                    db_file_name = basename + '.sqlite'
                else:
                    db_file_name = pool + '.sqlite'
        self.storage = sqlite.SQLiteStorage(db_file_name)
        config_loader = yaml_pool.YAMLPoolLoader(pool)
        hosts = config_loader.load()
        for host in hosts:

            # initial values for the hosts.
            # these will update over time.
            host.update({
                'alive': False,
                'reserved': False,
                'host_id': None
            })
            self.storage.add_host(host)

    def list_hosts(self):
        hosts = self.storage.get_hosts()
        return filter(lambda host: host['host_id'], hosts)

    def acquire_host(self):

        for host in self._get_free_hosts():

            # try reserving the host, we only update hosts that have a reserved
            # value of False in case some other thread has managed to reserve
            # this host before us.
            _, reserved = self.storage.update_host(
                host['global_id'],
                {'reserved': True},
                {'reserved': False,
                 'host_id': None})

            # if we didn't manage to reserve it,
            # continue to the next one
            if not reserved:
                continue

            # if we did manager to reserve it,
            # check its state
            host_alive = self._is_alive(host)

            # if the host is dead, delete the
            # reservation and move on
            if not host_alive:
                self.storage.update_host(
                    host['global_id'],
                    {'reserved': False})
                continue

            # if the host is alive, this is our host.
            if host_alive:
                hst, _ = self.storage.update_host(
                    host['global_id'],
                    {'reserved': False,
                     'host_id': str(uuid.uuid4())})
                self._load_keyfile(hst)
                return hst

        # we didn't manager to acquire any host
        raise exceptions.NoHostAvailableException()

    def release_host(self, host_id):
        host = self.get_host(host_id)
        self.storage.update_host(
            host['global_id'],
            {'host_id': None})
        return host

    def get_host(self, host_id):
        hosts = self.storage.get_hosts(host_id=host_id)
        if len(hosts) == 0:
            raise exceptions.HostNotFoundException(host_id)
        self._load_keyfile(hosts[0])
        return hosts[0]

    def _get_free_hosts(self):

        # note that this logic is simply an optimization.
        # it is very possible that right after we get the host list,
        # another thread will reserve or even acquire a host. therefore a
        # double check after this part is required anyway

        # first try living hosts,
        # then try dead hosts
        for alive in True, False:

            # in any case, we are only interested
            # in unreserved hosts that are not allocated
            # to anyone yet
            hosts = self.storage.get_hosts(
                host_id=None,
                reserved=False,
                alive=alive)
            for host in hosts:
                yield host

    @staticmethod
    def _is_alive(host):
        address, port = host['host'], host['port']
        results = scan.scan([(address, port)])
        return results[address, port]

    @staticmethod
    def _load_keyfile(host):
        if host['auth'].get('keyfile'):
            keyfile = host['auth']['keyfile']
            with open(keyfile) as f:
                content = f.read()
                host['auth']['keyfile'] = content
