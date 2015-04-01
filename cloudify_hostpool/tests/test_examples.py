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

import testtools
import os
import cloudify_hostpool
import requests
import tempfile
from requests.exceptions import ConnectionError


from cloudify.workflows import local


IGNORED_LOCAL_WORKFLOW_MODULES = (
    'worker_installer.tasks',
    'plugin_installer.tasks',
    'windows_agent_installer.tasks',
    'windows_plugin_installer.tasks'
)


class ExamplesTest(testtools.TestCase):

    def test_local_blueprint(self):

        tempdir = tempfile.mkdtemp(prefix='cloudify-host-pool-service')

        blueprint_path = os.path.join(
            os.path.dirname(os.path.dirname(cloudify_hostpool.__file__)),
            'examples',
            'local-blueprint.yaml'
        )

        env = local.init_env(
            blueprint_path=blueprint_path,
            inputs={'directory': tempdir, 'pool': 'pool.yaml'},
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)

        env.execute('install', task_retries=0)
        self._post_install_assertions()
        env.execute('uninstall')
        self._post_uninstall_assertions()

    def _post_install_assertions(self):

        # query the service to make sure its working
        response = requests.get('http://localhost:8080/hosts')
        hosts = response.json()['hosts']

        # no hosts were acquired
        self.assertEqual([], hosts)

    def _post_uninstall_assertions(self):

        # query the service to make sure its not working
        self.assertRaises(ConnectionError, requests.get,
                          'http://localhost:8080/hosts')
