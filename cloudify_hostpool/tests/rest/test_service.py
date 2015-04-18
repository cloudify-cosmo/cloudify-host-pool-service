# #######
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

import shutil
import tempfile
import os
import json

import testtools

from cloudify_hostpool.tests import rest


class ServiceTest(testtools.TestCase):

    _workdir = None

    def setUp(self):
        super(ServiceTest, self).setUp()
        self.original_dir = os.getcwd()
        self._workdir = tempfile.mkdtemp()
        os.chdir(self._workdir)
        config_file = os.path.join(
            os.path.dirname(rest.__file__),
            'resources',
            'host-pool.yaml'
        )
        os.environ['HOST_POOL_SERVICE_CONFIG_PATH'] = config_file
        from cloudify_hostpool.rest import service

        # flask feature, should provider more detailed errors
        service.app.config['TESTING'] = True

        # force database initial load
        service.reset_backend()
        self.app = service.app.test_client()

    def tearDown(self):
        super(ServiceTest, self).tearDown()
        os.chdir(self.original_dir)
        shutil.rmtree(self._workdir)

    def test_list_hosts(self):
        result = self.app.get('/hosts')
        self.assertEqual(result._status_code, 200)
        self.app.post('/hosts')
        result = self.app.get('/hosts')
        self.assertEqual(result._status_code, 200)
        hosts_list = json.loads(result.response.next())
        self.assertEqual(len(hosts_list), 1)

    def test_acquire(self):
        result = self.app.post('/hosts')
        self.assertEqual(result._status_code, 201)
        result = self.app.post('/hosts')
        self.assertEqual(result._status_code, 515)

    def test_get(self):
        result = self.app.get('/hosts/test')
        self.assertEqual(result._status_code, 404)
        result = self.app.post('/hosts')
        self.assertEqual(result._status_code, 201)
        host = json.loads(result.response.next())
        result = self.app.get('/hosts/{0}'.format(host['host_id']))
        self.assertEqual(result._status_code, 200)

    def test_acquire_and_release(self):
        result = self.app.post('/hosts')
        self.assertEqual(result._status_code, 201)
        host = json.loads(result.response.next())
        result = self.app.post('/hosts')
        self.assertEqual(result._status_code, 515)
        result = self.app.delete('/hosts/{0}'.format(host['host_id']))
        self.assertEqual(result._status_code, 200)
        result = self.app.post('/hosts')
        self.assertEqual(result._status_code, 201)
