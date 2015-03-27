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

import filelock
import uuid
import os

from cloudify_hostpool.hosts import scan
from cloudify_hostpool.storage import sqlite
from cloudify_hostpool.config import yaml_pool
from cloudify_hostpool import exceptions


# we currently don't expose these in the configuration because its somewhat
# internal. perhaps at a later time we can have this configurable, at which
# point we need to define the semantics of how to initialize the components.

FLock = filelock.FileLock('host-pool-backend.lock')

# if this file exists, loading of the pool will not take place.
# note that this means that multiple instances of this application that
# execute from the same directory will only load the pool the first
# time, and all other instances will use the previously loaded pool.
INDICATOR = 'host-pool-loaded-indicator'


class RestBackend(object):

    def __init__(self, pool, storage=None):
        self.storage = sqlite.SQLiteStorage(storage)
        # allow only one process to do the initial load

        def _create_indicator():
            fd = os.open(INDICATOR, os.O_WRONLY |
                         os.O_CREAT | os.O_EXCL, 0600)
            os.close(fd)

        with FLock:
            if not os.path.exists(INDICATOR):
                self._load_pool(pool)
                _create_indicator()

    def _load_pool(self, pool):
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

            try:

                # if we did manager to reserve it,
                # check its state
                host_alive = self._is_alive(host)

                # if the host is dead, delete the
                # reservation and move on
                if not host_alive:
                    self.storage.update_host(
                        host['global_id'],
                        {'reserved': False})
                    reserved = False
                    continue

                # if the host is alive, this is our host.
                if host_alive:
                    hst, _ = self.storage.update_host(
                        host['global_id'],
                        {'reserved': False,
                         'host_id': str(uuid.uuid4())})
                    reserved = False
                    self._load_keyfile(hst)
                    return hst

            finally:
                # if the host is still somehow reserved (unexpected exception
                # thrown), release it
                if reserved:
                    self.storage.update_host(
                        host['global_id'],
                        {'reserved': False})

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
