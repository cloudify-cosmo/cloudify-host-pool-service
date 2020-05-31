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
    cloudify_hostpool.tests.rest.test_service
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Tests for REST service
'''

# pylint: disable=R0904

import os
import mock
import json
import yaml
import httplib
import logging
import threading
import testtools

from ... import constants
from ...tests import rest


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


class ServiceTest(testtools.TestCase):
    '''Tests class for the REST service'''
    _workdir = None

    def setUp(self):
        testtools.TestCase.setUp(self)
        config_path = os.path.join(
            os.path.dirname(rest.__file__),
            'resources',
            'host-pool.yaml'
        )
        with open(config_path, 'r') as f_cfg:
            config = yaml.load(f_cfg)

        from ...rest import service

        # flask feature, should provider more detailed errors
        service.app.config['TESTING'] = True
        # configure Flask to Gunicorn logging
        gunicorn_handlers = logging.getLogger('gunicorn.error').handlers
        service.app.logger.handlers.extend(gunicorn_handlers)
        service.app.logger.info('Flask, Gunicorn logging enabled')
        # force database initial load
        service.reset_backend()
        self.app = service.app.test_client()
        self.app.post('/hosts',
                      data=json.dumps(config),
                      content_type='application/json')

    def tearDown(self):
        testtools.TestCase.tearDown(self)

    def test_add_host_no_data(self):
        '''Tests POSt /hosts with non-JSON data'''
        result = self.app.post('/hosts')
        self.assertEqual(result.status_code, httplib.BAD_REQUEST)

    def test_add_host_bad_format(self):
        '''Tests POSt /hosts with non-JSON data'''
        data = {
            'os': 'linux',
            'endpoint': {
                'protocol': 'ssh',
                'ip': '192.168.1.100',
                'port': 22
            },
            'credentials': {
                'username': 'mock',
                'password': 'mock-password'
            }
        }
        result = self.app.post('/hosts',
                               data=json.dumps(data))
        self.assertEqual(result.status_code, httplib.BAD_REQUEST)

    def test_get_hosts(self):
        '''Tests GET /hosts'''
        result = self.app.get('/hosts')
        self.assertEqual(result.status_code, httplib.OK)
        # Check the hosts themselves
        hosts = json.loads(result.data)
        self.assertIsInstance(hosts, list)
        for host in hosts:
            self.assertIsInstance(host, dict)
            self.assertIsNotNone(host[constants.HOST_ID_KEY])
            self.assertIsInstance(host[constants.HOST_ID_KEY], int)

    def test_get_hosts_filter(self):
        '''Tests GET /hosts with filters'''
        # Get all linux hosts
        result = self.app.get('/hosts?os=linux')
        self.assertEqual(result.status_code, httplib.OK)
        # Check the hosts themselves
        hosts = json.loads(result.data)
        self.assertIsInstance(hosts, list)
        self.assertEqual(len(hosts) > 0, True)
        for host in hosts:
            self.assertIsInstance(host, dict)
            self.assertIsNotNone(host[constants.HOST_ID_KEY])
            self.assertIsInstance(host[constants.HOST_ID_KEY], int)
        # Get all tagged hosts
        result = self.app.get('/hosts?tags=win_2008')
        self.assertEqual(result.status_code, httplib.OK)
        # Check the hosts themselves
        hosts = json.loads(result.data)
        self.assertIsInstance(hosts, list)
        self.assertEqual(len(hosts), 4)
        for host in hosts:
            self.assertIsInstance(host, dict)
            self.assertIsNotNone(host[constants.HOST_ID_KEY])
            self.assertIsInstance(host[constants.HOST_ID_KEY], int)
        # Get all tagged hosts list
        result = self.app.get('/hosts?tags=win_2008,test')
        self.assertEqual(result.status_code, httplib.OK)
        # Check the hosts themselves
        hosts = json.loads(result.data)
        self.assertIsInstance(hosts, list)
        self.assertEqual(len(hosts), 4)
        for host in hosts:
            self.assertIsInstance(host, dict)
            self.assertIsNotNone(host[constants.HOST_ID_KEY])
            self.assertIsInstance(host[constants.HOST_ID_KEY], int)

    def test_get_host(self):
        '''Tests GET /host/<host_id>'''
        result = self.app.get('/hosts')
        self.assertEqual(result.status_code, httplib.OK)
        hosts = json.loads(result.data)
        self.assertIsInstance(hosts, list)
        self.assertThat(len(hosts), testtools.matchers.GreaterThan(1))
        host_id = hosts[0][constants.HOST_ID_KEY]
        # Get the host
        result = self.app.get('/host/{0}'.format(host_id))
        self.assertEqual(result.status_code, httplib.OK)
        host = json.loads(result.data)
        self.assertIsInstance(host, dict)
        self.assertIsNotNone(host[constants.HOST_ID_KEY])
        self.assertIsInstance(host[constants.HOST_ID_KEY], int)

    def test_get_bad_request(self):
        '''Tests GET /host/<host_id> with a non-int ID'''
        result = self.app.get('/host/xyz123')
        self.assertEqual(result.status_code, httplib.NOT_FOUND)

    def test_get_bad_host(self):
        '''Tests GET /host/<host_id> with a non-existent host'''
        result = self.app.get('/host/999999')
        self.assertEqual(result.status_code, httplib.NOT_FOUND)

    def test_update_host(self):
        '''Tests PATCH /host/<host_id>'''
        # Get the list of hosts
        result = self.app.get('/hosts')
        self.assertEqual(result.status_code, httplib.OK)
        hosts = json.loads(result.data)
        self.assertIsInstance(hosts, list)
        self.assertThat(len(hosts), testtools.matchers.GreaterThan(1))
        host_id = hosts[0][constants.HOST_ID_KEY]
        # Update the host
        data = {'tags': ['hello', 'world']}
        result = self.app.patch('/host/{0}'.format(host_id),
                                data=json.dumps(data),
                                content_type='application/json')
        self.assertEqual(result.status_code, httplib.OK)
        # Check that the host updated
        result = self.app.get('/host/{0}'.format(host_id))
        self.assertEqual(result.status_code, httplib.OK)
        host = json.loads(result.data)
        self.assertIsInstance(host, dict)
        self.assertIsInstance(host.get('tags'), list)

    def test_delete_host(self):
        '''Tests DELETE /host/<host_id>'''
        # Get the list of hosts
        result = self.app.get('/hosts')
        self.assertEqual(result.status_code, httplib.OK)
        hosts = json.loads(result.data)
        self.assertIsInstance(hosts, list)
        self.assertThat(len(hosts), testtools.matchers.GreaterThan(1))
        host_count = len(hosts)
        host_id = hosts[0][constants.HOST_ID_KEY]
        # Delete the host
        result = self.app.delete('/host/{0}'.format(host_id))
        self.assertEqual(result.status_code, httplib.NO_CONTENT)
        # Check that the number of hosts went down by 1
        result = self.app.get('/hosts')
        self.assertEqual(result.status_code, httplib.OK)
        hosts = json.loads(result.data)
        self.assertIsInstance(hosts, list)
        self.assertEqual(len(hosts), host_count - 1)

    def test_delete_bad_host(self):
        '''Tests DELETE /host/<host_id> with a non-existent host'''
        result = self.app.delete('/host/999999')
        self.assertEqual(result.status_code, httplib.NOT_FOUND)

    def test_delete_bad_request(self):
        '''Tests DELETE /host/<host_id> with a non-int ID'''
        result = self.app.delete('/host/xyz123')
        self.assertEqual(result.status_code, httplib.NOT_FOUND)

    def allocate(self, data=None, req_os=None):
        '''allocate & deallocate helper'''
        # Allocate
        result = self.app.post('/host/allocate',
                               data=json.dumps(data),
                               content_type='application/json')
        self.assertEqual(result.status_code, httplib.OK)
        host = json.loads(result.data)
        self.assertIsInstance(host, dict)
        self.assertIsInstance(host[constants.HOST_ID_KEY], int)
        self.assertEqual(host['allocated'], True)
        if req_os:
            self.assertEqual(host['os'], req_os)
        # Deallocate
        result = self.app.delete('/host/{0}/deallocate'.format(
            host[constants.HOST_ID_KEY]))
        self.assertEqual(result.status_code, httplib.NO_CONTENT)
        # Double check deallocation
        result = self.app.get('/host/{0}'.format(
            host[constants.HOST_ID_KEY]))
        self.assertEqual(result.status_code, httplib.OK)
        host = json.loads(result.data)
        self.assertIsInstance(host, dict)
        self.assertIsInstance(host[constants.HOST_ID_KEY], int)
        self.assertEqual(host['allocated'], False)

    @mock.patch('cloudify_hostpool.rest.backend.RestBackend.host_port_scan',
                _mock_scan_alive)
    def test_allocate_windows(self):
        '''Tests allocate & deallocate with OS=Windows'''
        self.allocate(data={'os': 'windows'}, req_os='windows')

    @mock.patch('cloudify_hostpool.rest.backend.RestBackend.host_port_scan',
                _mock_scan_alive)
    def test_allocate_linux(self):
        '''Tests allocate & deallocate with OS=Linux'''
        self.allocate(data={'os': 'linux'}, req_os='linux')

    @mock.patch('cloudify_hostpool.rest.backend.RestBackend.host_port_scan',
                _mock_scan_alive)
    def test_allocate_no_os(self):
        '''Tests allocate & deallocate without OS'''
        self.allocate()

    @mock.patch('cloudify_hostpool.rest.backend.RestBackend.host_port_scan',
                _mock_scan_alive)
    def test_allocate_bad_os(self):
        '''Tests POST /host/allocate with bad OS'''
        result = self.app.post('/host/allocate',
                               data=json.dumps({'os': 'bados'}),
                               content_type='application/json')
        self.assertEqual(result.status_code, 515)
        response = json.loads(result.data)
        self.assertIn('error', response)
        self.assertIn('Cannot acquire host', response['error'])

    @mock.patch('cloudify_hostpool.rest.backend.RestBackend.host_port_scan',
                _mock_scan_alive)
    def test_allocate_bad_os_type(self):
        '''Tests POST /host/allocate with bad OS type'''
        result = self.app.post('/host/allocate',
                               data=json.dumps({'os': 1234}),
                               content_type='application/json')
        self.assertEqual(result.status_code, 515)
        response = json.loads(result.data)
        self.assertIn('error', response)
        self.assertIn('Cannot acquire host', response['error'])

    @mock.patch('cloudify_hostpool.rest.backend.RestBackend.host_port_scan',
                _mock_scan_alive)
    def test_allocate_bad_data_format(self):
        '''Tests POST /host/allocate without JSON header'''
        result = self.app.post('/host/allocate',
                               data="{'os': 'linux'}")
        self.assertEqual(result.status_code, httplib.BAD_REQUEST)
        response = json.loads(result.data)
        self.assertIn('error', response)
        self.assertIn('Unexpected data', response['error'])

    @mock.patch('cloudify_hostpool.rest.backend.RestBackend.host_port_scan',
                _mock_scan_dead)
    def test_allocate_no_free_host(self):
        '''Tests allocate with no available hosts'''
        result = self.app.post('/host/allocate')
        self.assertEqual(result.status_code, 515)
        response = json.loads(result.data)
        self.assertIn('error', response)
        self.assertIn('Cannot acquire host', response['error'])


class ServiceConcurrencyTest(testtools.TestCase):
    '''Tests class for the REST service using concurrency'''
    _workdir = None

    def setUp(self):
        testtools.TestCase.setUp(self)
        config_path = os.path.join(
            os.path.dirname(rest.__file__),
            'resources',
            'host-pool.yaml'
        )
        config = dict()
        with open(config_path, 'r') as f_cfg:
            config = yaml.load(f_cfg)

        from ...rest import service

        # flask feature, should provider more detailed errors
        service.app.config['TESTING'] = True
        # configure Flask to Gunicorn logging
        gunicorn_handlers = logging.getLogger('gunicorn.error').handlers
        service.app.logger.handlers.extend(gunicorn_handlers)
        service.app.logger.info('Flask, Gunicorn logging enabled')
        # force database initial load
        service.reset_backend()
        self.app = service.app.test_client()
        self.app.post('/hosts',
                      data=json.dumps(config),
                      content_type='application/json')

    def tearDown(self):
        testtools.TestCase.tearDown(self)

    def allocate_only(self, thread_id, retvals, data=None, req_os=None):
        '''allocate helper for threads'''
        # Allocate
        result = self.app.post('/host/allocate',
                               data=json.dumps(data),
                               content_type='application/json')
        self.assertEqual(result.status_code, httplib.OK)
        host = json.loads(result.data)
        self.assertIsInstance(host, dict)
        self.assertIsInstance(host[constants.HOST_ID_KEY], int)
        self.assertEqual(host['allocated'], True)
        if req_os:
            self.assertEqual(host['os'], req_os)
        retvals[thread_id] = host[constants.HOST_ID_KEY]

    def deallocate_all(self):
        '''Deallocates all hosts'''
        result = self.app.get('/hosts')
        hosts = json.loads(result.data)
        for host in hosts:
            # Deallocate
            result = self.app.delete('/host/{0}/deallocate'.format(
                host[constants.HOST_ID_KEY]))
            self.assertEqual(result.status_code, httplib.NO_CONTENT)
            # Double check deallocation
            result = self.app.get('/host/{0}'.format(
                host[constants.HOST_ID_KEY]))
            self.assertEqual(result.status_code, httplib.OK)
            host = json.loads(result.data)
            self.assertIsInstance(host, dict)
            self.assertIsInstance(host[constants.HOST_ID_KEY], int)
            self.assertEqual(host['allocated'], False)

    @mock.patch('cloudify_hostpool.rest.backend.RestBackend.host_port_scan',
                _mock_scan_alive)
    def test_multithread_acquire(self):
        '''Tests allocate with multiple threads'''
        # This should not exceed the number of hosts being acquired
        max_threads = 4
        threads = list()
        retvals = [None] * max_threads
        for thread_id in range(max_threads):
            threads.append(
                threading.Thread(
                    target=self.allocate_only,
                    args=(thread_id, retvals, {'os': 'linux'}, 'linux',)
                )
            )
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.deallocate_all()
        # Check if any threads could not acquire a host
        self.assertEqual(None in retvals, False)
        # Check if any threads ended up with the same host ID as another
        duplicate_hosts = set([x for x in retvals if retvals.count(x) > 1])
        self.assertEqual(len(duplicate_hosts), 0)
