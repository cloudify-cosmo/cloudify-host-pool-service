########
# Copyright (c) 2014-2019 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import json
import pytest

from ecosystem_tests.dorkl import (
    blueprints_upload,
    basic_blueprint_test,
    cleanup_on_failure, prepare_test
)

OS_VERSION = '3.2.15'
OS_WAGON = 'https://github.com/cloudify-cosmo/cloudify-openstack-plugin/' \
           'releases/download/{v}/cloudify_openstack_plugin-{v}-py27-none-' \
           'linux_x86_64-centos-Core.wgn'.format(v=OS_VERSION)
OS_PLUGIN = 'https://github.com/cloudify-cosmo/' \
            'cloudify-openstack-plugin/releases/download/' \
            '{v}/plugin.yaml'.format(v=OS_VERSION)
PLUGINS_TO_UPLOAD = [(OS_WAGON, OS_PLUGIN)]


SECRETS_TO_CREATE = {
    'openstack_username': False,
    'openstack_password': False,
    'openstack_tenant_name': False,
    'openstack_auth_url': False,
    'openstack_region': False,
    'openstack_region_name': False,
    'openstack_external_network': False,
    'openstack_project_id': False,
    'openstack_project_name': False,
    'openstack_project_domain_id': False,
    'openstack_user_domain_name': False,
    'openstack_project_domain_name': False,
    'base_image_id': False,
    'base_flavor_id': False,
}


prepare_test(plugins=PLUGINS_TO_UPLOAD,
             secrets=SECRETS_TO_CREATE,
             plugin_test=False)

virtual_machine_list = ['examples/blueprint.yaml']
infra_path = 'examples/blueprint-examples/virtual-machine/{0}.yaml'
infra_name = 'openstack'
inputs = 'infra_name={0}'.format(infra_name)


@pytest.fixture(scope='function', params=virtual_machine_list)
def blueprint_test(request):
    blueprints_upload(
        infra_path.format(infra_name),
        'infra-{0}'.format(infra_name))
    dirname_param = os.path.dirname(request.param).split('/')[-1:][0]
    try:
        basic_blueprint_test(
            request.param,
            dirname_param,
            inputs=inputs,
            timeout=3000
        )
    except:
        cleanup_on_failure(dirname_param)
        raise


def test_blueprint(blueprint_test):
    assert blueprint_test is None
