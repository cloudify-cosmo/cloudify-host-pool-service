########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
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
'''Cloudify Host-Pool Service package config'''

from setuptools import setup

setup(
    name='cloudify-host-pool-service',
    version='1.1.dev0',
    license='LICENSE',
    packages=['cloudify_hostpool',
              'cloudify_hostpool.tests',
              'cloudify_hostpool.storage',
              'cloudify_hostpool.rest'],
    package_data={'cloudify_hostpool': ['resources/service_init.sh']},
    description='Cloudify Host Pool Service',
    install_requires=[
        'flask',
        'flask_restful',
        'PyYAML==3.10',
        'netaddr',
        'requests==2.7.0',
        'filelock==0.2.0',
        'tinydb'
    ]
)
