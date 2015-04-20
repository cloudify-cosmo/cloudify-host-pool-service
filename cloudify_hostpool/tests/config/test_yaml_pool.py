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

import os
import tempfile
import testtools

from cloudify_hostpool.config import yaml_pool
from cloudify_hostpool import exceptions


class YAMLPoolLoaderTest(testtools.TestCase):

    def test_get_broadcast(self):
        ip = '123.213.123.232'
        mask = '30'
        self.assertEqual(
            '123.213.123.235',
            yaml_pool._long2ip(yaml_pool._get_broadcast_long(ip, mask)))

    def test_get_subnet_and_mask(self):
        ip = '123.213.123.232/30'
        self.assertEqual(('123.213.123.232', '30'),
                         yaml_pool._get_subnet_and_mask(ip))

    def test_get_subnet_and_mask_wrong_ip(self):
        ip = '123.213.123.232dasfsdf'
        self.assertRaises(exceptions.ConfigurationError,
                          yaml_pool._get_subnet_and_mask, ip)
        ip = '123.213..232/30'
        self.assertRaises(exceptions.ConfigurationError,
                          yaml_pool._get_subnet_and_mask, ip)
        ip = 'dasfsdf'
        self.assertRaises(exceptions.ConfigurationError,
                          yaml_pool._get_subnet_and_mask, ip)

    def test_get_subnet_hosts(self):
        subnet = '2.2.2.0'
        mask = '29'
        ips = list(yaml_pool._get_subnet_hosts(subnet, mask))
        self.assertEqual(len(ips), 6)

        subnet = '2.2.2.8'
        mask = '29'
        ips = list(yaml_pool._get_subnet_hosts(subnet, mask))
        self.assertEqual(len(ips), 6)

        subnet = '2.2.2.16'
        mask = '29'
        ips = list(yaml_pool._get_subnet_hosts(subnet, mask))
        self.assertEqual(len(ips), 6)

        subnet = '2.2.2.248'
        mask = '29'
        ips = list(yaml_pool._get_subnet_hosts(subnet, mask))
        self.assertEqual(len(ips), 6)

    def test_load_host(self):
        hosts = [
            dict(host='2.2.2.1', port=22,
                 auth={'username': 'ubuntu', 'pass': 'pass2'}),
            dict(host='2.2.2.2', port=22,
                 auth={'username': 'ubuntu2', 'pass': 'pass2'})
        ]

        pool = yaml_pool.YAMLPoolLoader({
            'hosts': hosts
        })
        saved_hosts = list(pool.load())
        self.assertEqual(len(saved_hosts), len(hosts))

    def test_load_ip_range(self):
        hosts = [
            dict(ip_range='2.2.2.8/29',
                 auth={'username': 'ubuntu3', 'pass': 'pass2'}, port=22)
        ]
        pool = yaml_pool.YAMLPoolLoader({
            'hosts': hosts
        })
        saved_hosts = list(pool.load())
        self.assertEqual(len(saved_hosts), 6)

    def test_load_no_host_no_ip_range(self):
        hosts = [
            {
                'auth': {'username': 'ubuntu3', 'pass': 'pass2'},
                'port': 22
            }
        ]
        pool = yaml_pool.YAMLPoolLoader({'hosts': hosts})
        self.assertRaisesRegexp(
            exceptions.ConfigurationError,
            "A host must define either the 'host' or the 'ip_range' key",
            lambda: list(pool.load()))

    def test_load_unsupported_host_key(self):
        hosts = [
            dict(ip='2.2.2.8',
                 auth={'username': 'ubuntu3', 'pass': 'pass2'}, port=22)
        ]
        pool = yaml_pool.YAMLPoolLoader({'hosts': hosts})
        self.assertRaisesRegexp(
            exceptions.ConfigurationError,
            "A host must define either the 'host' or the 'ip_range' key",
            lambda: list(pool.load()))

    def test_load_no_port(self):
        hosts = [
            dict(host='2.2.2.8',
                 auth={'username': 'ubuntu3', 'pass': 'pass2'})
        ]
        pool = yaml_pool.YAMLPoolLoader({'hosts': hosts})
        self.assertRaisesRegexp(
            exceptions.ConfigurationError,
            "Port not provided for host: 2.2.2.8",
            lambda: list(pool.load()))

        hosts = [
            dict(ip_range='2.2.2.8/29')
        ]
        pool = yaml_pool.YAMLPoolLoader(
            {
                'hosts': hosts,
                'default': {
                    'auth': {
                        'username': 'adam',
                        'password': 'eve'
                    }
                }
            })
        self.assertRaisesRegexp(
            exceptions.ConfigurationError,
            'Port not provided for host: 2.2.2.9',
            lambda: list(pool.load()))

    def test_load_no_auth(self):
        hosts = [
            dict(host='2.2.2.8',
                 port=22)
        ]
        pool = yaml_pool.YAMLPoolLoader({'hosts': hosts})
        self.assertRaisesRegexp(
            exceptions.ConfigurationError,
            'Authentication not provided for host: 2.2.2.8',
            lambda: list(pool.load()))

    def test_load_config(self):
        _file = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 'resources/pool.yaml')
        pool = yaml_pool.YAMLPoolLoader(_file)
        loaded_hosts = list(pool.load())
        self.assertEqual(len(loaded_hosts), 4)

    def test_bad_config(self):
        bad_config = {
            'bad_key': {
                'bad_key': 'test'
            }
        }
        self.assertRaisesRegexp(
            exceptions.ConfigurationError,
            'Pool configuration is missing a hosts section',
            yaml_pool.YAMLPoolLoader, bad_config)

    def test_wrong_config_type(self):
        self.assertRaisesRegexp(
            exceptions.ConfigurationError,
            "Unexpected configuration type: <type 'tuple'>",
            yaml_pool.YAMLPoolLoader, ('test', ))

    def test_empty_config(self):
        self.assertRaisesRegexp(
            exceptions.ConfigurationError,
            'Pool configuration is missing a hosts section',
            yaml_pool.YAMLPoolLoader, {})

    def test_bad_keyfile(self):
        tmp_dir = tempfile.mkdtemp()
        config = {'default': {'auth': {'username': 'x'}, 'port': 123},
                  'hosts': [{'host': 'google.com',
                             'auth': {'username': 'x',
                                      'keyfile': tmp_dir + '/wrong_file'},
                             'port': 80}]}
        try:
            pool = yaml_pool.YAMLPoolLoader(config)
            self.assertRaisesRegexp(exceptions.ConfigurationError,
                                    'does not exist or does not have the '
                                    'proper permissions', pool.load().next)
        finally:
            os.rmdir(tmp_dir)

    def test_good_keyfile(self):
        fd, good_file = tempfile.mkstemp()
        os.close(fd)
        config = {'default': {'auth': {'username': 'x'}, 'port': 123},
                  'hosts': [{'host': 'google.com',
                             'auth': {'username': 'x',
                                      'keyfile': good_file},
                             'port': 80}]}
        try:
            config_loader = yaml_pool.YAMLPoolLoader(config)
            self.assertEquals(config_loader.load().next(),
                              dict(host='google.com',
                                   auth=dict(username='x',
                                             keyfile=good_file),
                                   port=80,
                                   public_address=None))
        finally:
            os.unlink(good_file)

    def test_merge_auth_dictionary(self):

        hosts = [
            dict(host='2.2.2.8',
                 auth={'password': 'pass2'},
                 port=22)
        ]

        pool = yaml_pool.YAMLPoolLoader(
            {
                'hosts': hosts,
                'default': {
                    'auth': {
                        'username': 'adam'
                    }
                }
            })
        host = pool.load().next()
        self.assertEqual(host['auth']['username'], 'adam')
        self.assertEqual(host['auth']['password'], 'pass2')
