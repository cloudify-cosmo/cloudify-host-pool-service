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
    tests.examples
    ~~~~~~~~~~~~~~
    Tests the install / uninstall of the service
'''

import testtools
from testtools import matchers
import os
import cloudify_hostpool
import requests
import tempfile
import shutil

from requests.exceptions import ConnectionError
from cloudify.workflows import local


IGNORED_LOCAL_WORKFLOW_MODULES = (
    'worker_installer.tasks',
    'plugin_installer.tasks',
    'windows_agent_installer.tasks',
    'windows_plugin_installer.tasks',
    'cloudify_agent.operations',
    'cloudify_agent.installer.operations'
)


class ExamplesTest(testtools.TestCase):
    '''Class for testing the service lifecycles'''
    def setUp(self):
        testtools.TestCase.setUp(self)
        self.workdir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.workdir)

    def tearDown(self):
        testtools.TestCase.tearDown(self)
        os.chdir(self.original_dir)
        shutil.rmtree(self.workdir)

    def test_local_blueprint(self):
        '''Execute a local blueprint using the service'''
        # Create a directory to act as the working directory
        tempdir = tempfile.mkdtemp(prefix='cloudify-host-pool-service')
        # Build the path to the blueprint
        blueprint_path = os.path.join(
            os.path.dirname(os.path.dirname(cloudify_hostpool.__file__)),
            'examples',
            'local-blueprint',
            'local-blueprint.yaml'
        )
        # Init the local workflow environment
        env = local.init_env(
            blueprint_path=blueprint_path,
            inputs={
                'working_directory': tempdir,
                'run_as_daemon': False
            },
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)
        # Execute the "install" workflow
        env.execute('install', task_retries=0)
        self._post_install_assertions()
        # Execute the "uninstall" workflow
        env.execute('uninstall')
        self._post_uninstall_assertions()

    def _post_install_assertions(self):
        '''Test for basic service operation'''
        # query the service to make sure its working
        response = requests.get('http://localhost:8080/hosts')
        hosts = response.json()
        self.assertIsNotNone(hosts)
        self.assertIsInstance(hosts, list)
        self.assertThat(len(hosts), matchers.GreaterThan(0))

    def _post_uninstall_assertions(self):
        '''Test for basic service teardown'''
        # query the service to make sure its not working
        self.assertRaises(ConnectionError, requests.get,
                          'http://localhost:8080/hosts')
