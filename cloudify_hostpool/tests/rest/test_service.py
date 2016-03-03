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

import os
import testtools
import mock
import json
import yaml
import httplib
import logging

from cloudify_hostpool import constants
from cloudify_hostpool.tests import rest


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
        config = dict()
        with open(config_path, 'r') as f_cfg:
            config = yaml.load(f_cfg)

        from cloudify_hostpool.rest import service

        # flask feature, should provider more detailed errors
        service.app.config['TESTING'] = True
        # configure Flask to Gunicorn logging
        gunicorn_handlers = logging.getLogger('gunicorn.error').handlers
        service.app.logger.handlers.extend(gunicorn_handlers)
        service.app.logger.info('Flask, Gunicorn logging enabled')
        # force database initial load
        print 'START reset_backend()'
        service.reset_backend()
        print 'END reset_backend()'
        self.app = service.app.test_client()
        self.app.post('/hosts',
                      data=json.dumps(config),
                      content_type='application/json')

    def tearDown(self):
        testtools.TestCase.tearDown(self)

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
        print 'result: {0}, {1}'.format(result, result.status_code)
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

    @mock.patch('cloudify_hostpool.rest.backend.RestBackend.host_port_scan',
                _mock_scan_alive)
    def test_allocate_bad_os_type(self):
        '''Tests POST /host/allocate with bad OS type'''
        result = self.app.post('/host/allocate',
                               data=json.dumps({'os': 1234}),
                               content_type='application/json')
        self.assertEqual(result.status_code, 515)

    @mock.patch('cloudify_hostpool.rest.backend.RestBackend.host_port_scan',
                _mock_scan_dead)
    def test_allocate_no_free_host(self):
        '''Tests allocate with no available hosts'''
        result = self.app.post('/host/allocate')
        self.assertEqual(result.status_code, 515)
