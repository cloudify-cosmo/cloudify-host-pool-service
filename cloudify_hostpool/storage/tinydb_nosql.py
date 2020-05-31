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
    cloudify_hostpool.storage.tinydb
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    TinyDB NoSQL storage interface for the RESTful service
'''

import filelock
from contextlib import contextmanager

from tinydb import TinyDB

from .. import constants
from ..storage.base import Storage

LOCK_FILE = 'db_ops.lck'
DB_FILENAME = 'db_hostpool.json'
TBL_HOSTS = 'hosts'


def locked(func):
    '''Decorate to provide locking'''
    def wrapper(*args, **kwargs):
        '''Post processor'''
        with filelock.FileLock(LOCK_FILE):
            return func(*args, **kwargs)
    return wrapper


def postprocess_host(func):
    '''Decorator to force consistent returns'''
    def wrapper(*args, **kwargs):
        '''Post processor'''
        host = func(*args, **kwargs)
        # Fix a bad return
        if not host or \
           not isinstance(host, dict) or \
           not hasattr(host, 'eid'):
            return dict()
        # Assign a standard ID
        host[constants.HOST_ID_KEY] = host.eid
        return host
    return wrapper


def postprocess_hosts(func):
    '''Decorator to force consistent returns'''
    def wrapper(*args, **kwargs):
        '''Post processor'''
        hosts = func(*args, **kwargs)
        # Fix a bad return
        if not hosts or not isinstance(hosts, list):
            return list()
        # Assign standard IDs
        hosts = [x for x in hosts if hasattr(x, 'eid')]
        for host in hosts:
            host[constants.HOST_ID_KEY] = host.eid
        return hosts
    return wrapper


def postprocess_host_id(func):
    '''Decorator to force consistent returns'''
    def wrapper(*args, **kwargs):
        '''Post processor'''
        host_id = func(*args, **kwargs)
        # Fix the return value
        if isinstance(host_id, list) and len(host_id) == 1:
            return host_id[0]
        elif isinstance(host_id, int):
            return host_id
        return None
    return wrapper


class Database(Storage):
    '''
    Storage wrapper for TinyDB NoSQL DB implementing AbstractStorage interface
    '''
    def __init__(self, storage=None):
        self.db_filename = storage or DB_FILENAME
        self.tbl_hosts = TBL_HOSTS

    def init_data(self):
        '''Wipes all data'''
        with self.connect() as dbc:
            tbl = dbc.table(self.tbl_hosts)
            tbl.purge()

    @contextmanager
    def connect(self):
        '''Get a connection to the database'''
        yield TinyDB(self.db_filename)

    @postprocess_host
    def get_host(self, eid):
        '''Retrieves a single, specified host

        :param int eid: Host ID of the host to retrieve
        :returns: Host object
        :rtype: dict
        '''
        with self.connect() as dbc:
            tbl = dbc.table(self.tbl_hosts)
            return tbl.get(eid=eid)

    @postprocess_hosts
    @locked
    def get_hosts(self):
        '''Retrieves all host entries from the database

        :returns: A list of all host entries from the database
        :rtype: list
        '''
        with self.connect() as dbc:
            tbl = dbc.table(self.tbl_hosts)
            return tbl.all()

    def add_hosts(self, hosts):
        '''Adds multiple host entries to the database

        :param list hosts: List of host objects to add to the database
        :returns: List of new host IDs (integers)
        :rtype: list
        '''
        with self.connect() as dbc:
            tbl = dbc.table(self.tbl_hosts)
            return tbl.insert_multiple(hosts)

    @postprocess_host_id
    def update_host(self, eid, host):
        '''Updates an existing host in the database

        This will raise a KeyError exception if a non-existent
        host ID is provided.

        :param int eid: Host ID of the host to update
        :returns: Host ID that was updated (or None)
        :rtype: int
        '''
        with self.connect() as dbc:
            tbl = dbc.table(self.tbl_hosts)
            return tbl.update(host, eids=[eid])

    @postprocess_host_id
    def remove_host(self, eid):
        '''Removes an existing host from the database

        This will raise a KeyError exception if a non-existent
        host ID is provided.

        :param int eid: Host ID of the host to remove
        :returns: Host ID that was removed (or None if not found)
        :rtype: int
        '''
        with self.connect() as dbc:
            tbl = dbc.table(self.tbl_hosts)
            try:
                return tbl.remove(eids=[eid])
            except KeyError:
                return None
