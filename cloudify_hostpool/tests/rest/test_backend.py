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
import tempfile
import threading
import testtools
import shutil
from contextlib import contextmanager
from multiprocessing import process

import mock

from cloudify_hostpool import exceptions
from cloudify_hostpool.rest.backend import RestBackend


def _mock_scan_alive(endpoints, _=None):
    result = {}
    for endpoint in endpoints:
        result[endpoint[0], endpoint[1]] = True
    return result


def _mock_scan_dead(endpoints, _=None):
    result = {}
    for endpoint in endpoints:
        result[endpoint[0], endpoint[1]] = False
    return result


class RestBackendTest(testtools.TestCase):

    NUMBER_OF_HOSTS = 5

    def setUp(self):
        super(RestBackendTest, self).setUp()
        self._workdir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self._workdir)
        self.backend = self._init_backend()

    def tearDown(self):
        super(RestBackendTest, self).tearDown()
        os.chdir(self.original_dir)
        shutil.rmtree(self._workdir)

    def _init_backend(self, hosts=None):
        if hosts is None:
            hosts = self._generate_hosts(self.NUMBER_OF_HOSTS)
        return RestBackend(pool={'hosts': hosts})

    @contextmanager
    def _backend(self, hosts=None, chdir=True):

        """
        this context manager is meant for tests that require backend
        instantiation in addition to the one that happens in setUp.
        """

        # we will usually want to change directory when we initialize an
        # instance of the backend class. this is because if the instance is
        # instantiated from within a directory where a previous
        # instantiation happened, then the pool loading will not happen.
        # this is because this directory will contain the initial load
        # indicator file which will prevent additional loading.
        # see cloudify_hostpool.rest.backend

        workdir = tempfile.mkdtemp()
        if chdir:
            os.chdir(workdir)
        yield self._init_backend(hosts=hosts)
        shutil.rmtree(workdir)

    def _generate_hosts(self, count):
        return map(lambda i: {
            'host': 'host{0}'.format(i),
            'port': i + 1,
            'auth': {'username': 'username{0}'.format(i),
                     'password': 'password{0}'.format(i)},
            'public_address': 'public_address{0}'.format(i)
        }, range(0, count))

    def test_list_hosts(self):
        self.backend.storage.update_host(1, {'host_id': 'test'})
        self.assertEqual(len(self.backend.list_hosts()), 1)

    def test_release_host(self):
        self.backend.storage.update_host(1, {'host_id': 'test'})
        host = self.backend.release_host('test')

        # test release returns the previous value
        self.assertEqual(host['host_id'], 'test')

        # test host was really released
        hosts = self.backend.storage.get_hosts(host_id='test')
        self.assertEqual(len(hosts), 0)

    def test_release_non_existing_host(self):
        host_id = 'test'
        self.assertRaises(exceptions.HostNotFoundException,
                          self.backend.release_host, host_id)

    def test_get_host(self):
        host_id = 'test'
        self.backend.storage.update_host(1, {'host_id': host_id})
        host = self.backend.get_host(host_id)
        self.assertEqual(host['host_id'], host_id)

    def test_get_non_existing_host(self):
        self.assertRaises(exceptions.HostNotFoundException,
                          self.backend.get_host, 'host')

    @mock.patch('cloudify_hostpool.rest.backend.scan.scan',
                _mock_scan_alive)
    def test_acquire_host(self):
        host = self.backend.acquire_host()
        self.assertIsNotNone(host)

    @mock.patch('cloudify_hostpool.rest.backend.scan.scan',
                _mock_scan_alive)
    def test_acquire_all_hosts_sequentially(self):
        hosts = set()
        for i in range(self.NUMBER_OF_HOSTS):
            host = self.backend.acquire_host()
            hosts.add(host['global_id'])
        self.assertEqual(self.NUMBER_OF_HOSTS, len(hosts))

    @mock.patch('cloudify_hostpool.rest.backend.scan.scan',
                _mock_scan_alive)
    def test_acquire_all_hosts_concurrently(self):

        hosts = set()
        threads = []

        def _acquire():
            host = self.backend.acquire_host()
            hosts.add(host['global_id'])

        for i in range(self.NUMBER_OF_HOSTS):
            thread = threading.Thread(target=_acquire)
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(self.NUMBER_OF_HOSTS, len(hosts))

    @mock.patch('cloudify_hostpool.rest.backend.scan.scan',
                _mock_scan_alive)
    def test_acquire_more_threads_than_hosts(self):

        hosts = set()
        errors = []
        threads = []

        def _acquire():
            try:
                host = self.backend.acquire_host()
                hosts.add(host['global_id'])
            except exceptions.NoHostAvailableException as e:
                errors.append(e)

        for i in range(self.NUMBER_OF_HOSTS + 2):
            thread = threading.Thread(target=_acquire)
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(2, len(errors))
        self.assertEqual(self.NUMBER_OF_HOSTS, len(hosts))

    @mock.patch('cloudify_hostpool.rest.backend.scan.scan',
                _mock_scan_dead)
    def test_acquire_all_hosts_dead(self):
        self.assertRaises(exceptions.NoHostAvailableException,
                          self.backend.acquire_host)

    @mock.patch('cloudify_hostpool.rest.backend.scan.scan',
                _mock_scan_alive)
    def test_get_keyfile(self):

        """
        Test checking if key is properly read from the file and attached to
        the host structure instead of the key's file path.
        """

        key_mock = 'test_key'
        keyfile = os.path.join(self._workdir, 'key.pem')
        host_with_key = {
            'host': '127.0.0.1',
            'port': '22',
            'auth': {'username': 'user', 'keyfile': keyfile}
        }

        with open(keyfile, 'w') as f:
            f.write(key_mock)

        # a new instance of RestBackend is being created to make sure that
        # there is one and only host in storage with given key content that
        # is to be acquired.

        with self._backend(hosts=[host_with_key]) as backend:
            host = backend.acquire_host()
            self.assertEqual(host['auth']['keyfile'], key_mock)
            host = backend.get_host(host['host_id'])
            self.assertEqual(host['auth']['keyfile'], key_mock)

    def test_concurrent_initialization(self):

        processes = []

        os.chdir(tempfile.mkdtemp())

        def _initialize():
            self._init_backend()

        for i in range(20):
            # we use processes here instead of threads because file locks do
            # not respect thread access. this simulates a scenario where
            # gunicorn (or any other container) runs this flask application
            # with multiple workers
            p = process.Process(target=_initialize)
            processes.append(p)

        for p in processes:
            p.start()

        for p in processes:
            p.join()

        # connect to the underlying storage to make assertions
        backend = self._init_backend()
        self.assertEqual(len(backend.storage.get_hosts()),
                         self.NUMBER_OF_HOSTS)

    def test_sequentual_initialization(self):

        # this changes directory and initializes
        with self._backend() as backend1:

            # now initialize another instance from the same directory
            backend2 = self._init_backend()

            # assert pool loading was done only once
            self.assertEqual(backend1.storage._filename,
                             backend2.storage._filename)
            self.assertEqual(backend1.storage.get_hosts(),
                             backend2.storage.get_hosts())
            self.assertEqual(len(backend1.storage.get_hosts()),
                             self.NUMBER_OF_HOSTS)
