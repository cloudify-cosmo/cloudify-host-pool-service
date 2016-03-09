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
    cloudify_hostpool.tests.rest.test_backend
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Tests for REST backend service
'''

import testtools
from testtools import matchers
import mock

from cloudify_hostpool import constants, exceptions
from cloudify_hostpool.rest.backend import RestBackend


def _mock_scan_alive(self, _):
    '''Simulates all hosts being "alive"'''
    if self and self.logger:
        self.logger.debug('_mock_scan_alive()')
    return True


def _mock_scan_dead(self, _):
    '''Simulates all hosts being "dead"'''
    if self and self.logger:
        self.logger.debug('_mock_scan_dead()')
    return False


class RestBackendTest(testtools.TestCase):
    '''Test class for REST backend service'''
    NUMBER_OF_HOSTS = 5

    def setUp(self):
        testtools.TestCase.setUp(self)
        self.backend = RestBackend(reset_storage=True)
        hosts = self._generate_hosts(self.NUMBER_OF_HOSTS)
        self.backend.add_hosts({'hosts': hosts})

    def tearDown(self):
        testtools.TestCase.tearDown(self)
        del self.backend

    @staticmethod
    def _generate_hosts(count):
        '''Generate a list of hosts'''
        return [{
            'name': 'test-host-{0}'.format(idx + 10),
            'os': 'linux',
            'endpoint': {
                'ip': '172.16.0.{0}'.format(idx + 10),
                'port': 22,
                'protocol': 'ssh'
            },
            'credentials': {
                'username': 'ubuntu',
                'password': 'p4ssw0rd'
            },
            'tags': ['test_{0}'.format(idx)]
        } for idx in range(count)]

    def test_list_hosts(self):
        '''Test the number of existing entries'''
        self.assertEqual(len(self.backend.list_hosts()),
                         self.NUMBER_OF_HOSTS)
        self.assertEqual(
            len(self.backend.list_hosts(filters={'tags': ['test_0']})), 1)
        self.assertEqual(
            len(self.backend.list_hosts(filters={'tags': ['test_x']})), 0)
        self.assertEqual(
            len(self.backend.list_hosts(filters={
                'tags': ['test_0', 'test_x']})), 0)

    def test_add_host_invalid(self):
        '''Test various invalid attempts at adding a host'''
        # Test with no hosts
        self.assertRaises(
            exceptions.HostPoolHTTPException,
            self.backend.add_hosts, {'default': {'os': 'linux'}})
        # Test with invalid default type
        self.assertRaises(
            exceptions.ConfigurationError,
            self.backend.add_hosts, {
                'default': [{'os': 'linux'}],
                'hosts': [{
                    'os': 'windows',
                    'credentials': {
                        'username': 'foo',
                        'password': 'bar'
                    }
                }]
            })
        # Test with invalid endpoint type
        self.assertRaises(
            exceptions.ConfigurationError,
            self.backend.add_hosts, {
                'default': {'endpoint': 1234},
                'hosts': [{
                    'os': 'windows',
                    'credentials': {
                        'username': 'foo',
                        'password': 'bar'
                    }
                }]
            })
        # Test with invalid default keys present and invalid endpoint
        self.assertRaises(
            exceptions.ConfigurationError,
            self.backend.add_hosts, {
                'default': {
                    'os': 'linux',
                    'platform': {'foo': 'bar'},
                    'endpoint': {'ip': '123.123.123.123'}
                },
                'hosts': [{
                    'os': 'windows',
                    'credentials': {
                        'username': 'foo',
                        'password': 'bar'
                    }
                }]
            })
        # Test with unknown OS
        self.assertRaises(
            exceptions.ConfigurationError,
            self.backend.add_hosts, {'hosts': [{'os': 'solaris'}]})
        # Test without an endpoint
        self.assertRaises(
            exceptions.ConfigurationError,
            self.backend.add_hosts, {
                'hosts': [{
                    'os': 'windows',
                    'credentials': {
                        'username': 'foo',
                        'password': 'bar'
                    }
                }]
            })
        # Test with invalid tags
        self.assertRaises(
            exceptions.ConfigurationError,
            self.backend.add_hosts, {
                'hosts': [{
                    'os': 'windows',
                    'credentials': {
                        'username': 'foo',
                        'password': 'bar'
                    },
                    'endpoint': {'ip': '123.123.123.123'},
                    'tags': {'foo': 'bar'}
                }]
            })

    @mock.patch('cloudify_hostpool.rest.backend.RestBackend.host_port_scan',
                _mock_scan_alive)
    def test_acquire_host(self):
        '''Test acquire & release a host'''
        # Aquire the host
        host = self.backend.acquire_host()
        self.assertIsNotNone(host)
        self.assertIsNotNone(host[constants.HOST_ID_KEY])
        self.assertEqual(host['allocated'], True)
        # Release the host
        host = self.backend.release_host(host[constants.HOST_ID_KEY])
        self.assertIsNotNone(host)
        self.assertIsNotNone(host[constants.HOST_ID_KEY])
        self.assertEqual(host['allocated'], False)

    @mock.patch('cloudify_hostpool.rest.backend.RestBackend.host_port_scan',
                _mock_scan_alive)
    def test_acquire_host_filter(self):
        '''Test acquire & release a host with tag filter'''
        # Aquire the host
        host = self.backend.acquire_host(filters={'tags': ['test_1']})
        self.assertIsNotNone(host)
        self.assertIsNotNone(host[constants.HOST_ID_KEY])
        self.assertEqual(host['allocated'], True)
        # Release the host
        host = self.backend.release_host(host[constants.HOST_ID_KEY])
        self.assertIsNotNone(host)
        self.assertIsNotNone(host[constants.HOST_ID_KEY])
        self.assertEqual(host['allocated'], False)

    @mock.patch('cloudify_hostpool.rest.backend.RestBackend.host_port_scan',
                _mock_scan_alive)
    def test_acquire_host_filter_bad(self):
        '''Test acquire & release a host with bad tag filter'''
        self.assertRaises(exceptions.NoHostAvailableException,
                          self.backend.acquire_host,
                          filters={'tags': ['test_1', 'test_x']})
        self.assertRaises(exceptions.NoHostAvailableException,
                          self.backend.acquire_host,
                          filters={'tags': ['test_x']})

    @mock.patch('cloudify_hostpool.rest.backend.RestBackend.host_port_scan',
                _mock_scan_dead)
    def test_allocate_none_available(self):
        '''Test allocate without any available hosts'''
        self.assertRaises(exceptions.NoHostAvailableException,
                          self.backend.acquire_host)

    def test_get_host(self):
        '''Test retrieve a host'''
        hosts = self.backend.list_hosts()
        self.assertIsNotNone(hosts)
        self.assertIsInstance(hosts, list)
        self.assertThat(len(hosts), matchers.GreaterThan(2))
        host = self.backend.get_host(hosts[0][constants.HOST_ID_KEY])
        self.assertIsNotNone(host)
        self.assertIsNotNone(host[constants.HOST_ID_KEY])

    def test_release_non_existing_host(self):
        '''Test release a non-existent host'''
        self.assertRaises(exceptions.HostNotFoundException,
                          self.backend.release_host, 'test')

    def test_get_non_existing_host(self):
        '''Test retrieve a non-existent host'''
        self.assertRaises(exceptions.HostNotFoundException,
                          self.backend.get_host, 'test')
