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
import re
import socket
import struct
import copy

import yaml

from cloudify_hostpool.config.base import Loader
from cloudify_hostpool import exceptions

CIDR_REGEX = '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}'


class YAMLPoolLoader(Loader):

    def __init__(self, pool):
        config = self._load(pool)
        self._validate(config)
        self.default = config.get('default', {})
        self.hosts = config['hosts']

    def load(self):

        def _create_host(_host):

            if not auth:
                raise exceptions.ConfigurationError(
                    'Authentication not provided '
                    'for host: {0}'.format(_host))
            if not port:
                raise exceptions.ConfigurationError(
                    'Port not provided for host: {0}'
                    .format(_host))
            return {
                'auth': auth,
                'port': port,
                'host': _host,
                'public_address': public_address
            }

        for host in self.hosts:

            port = self._get_port(host)
            auth = self._get_auth(host)
            public_address = host.get('public_address')

            if 'host' in host:

                # an explicit address is configured for this host
                yield _create_host(host['host'])

            elif 'ip_range' in host:

                # ip range was specified. in this case we create a host
                # dictionary for each ip address separately.
                subnet, mask = _get_subnet_and_mask(host['ip_range'])
                for host_ip in _get_subnet_hosts(subnet, mask):
                    yield _create_host(host_ip)
            else:
                raise exceptions.ConfigurationError(
                    "A host must define either the "
                    "'host' or the 'ip_range' key")

    def _get_auth(self, host):

        default_auth = self.default.get('auth', {})
        auth = copy.deepcopy(default_auth)
        auth.update(host.get('auth', {}))
        keyfile = auth.get('keyfile')
        if keyfile and not os.access(keyfile, os.R_OK):
            raise exceptions.ConfigurationError(
                'Key file {0} does not exist or does not have '
                'the proper permissions'.format(keyfile))
        return auth

    def _get_port(self, host):
        return host.get('port') or self.default.get('port')

    @staticmethod
    def _load(pool):
        if isinstance(pool, str):
            with open(pool, 'r') as config_file:
                return yaml.load(config_file)
        elif isinstance(pool, dict):
            return pool
        else:
            raise exceptions.ConfigurationError(
                'Unexpected configuration '
                'type: {0}'.format(type(pool)))

    @staticmethod
    def _validate(config):
        if 'hosts' not in config:
            raise exceptions.ConfigurationError(
                'Pool configuration '
                'is missing a hosts section')


def _ip2long(ip):
    # raises socket.error if IP is not valid
    return struct.unpack('!L', socket.inet_aton(ip))[0]


def _long2ip(num):
    return socket.inet_ntoa(struct.pack('!L', num))


def _get_ibitmask(mask):
    return (2L << (32 - int(mask)) - 1) - 1


def _get_broadcast_long(subnet, mask):
    bin_sub = _ip2long(subnet)
    bin_imask = _get_ibitmask(int(mask))
    return bin_sub | bin_imask


def _get_subnet_and_mask(ip_range):
    regex = re.compile(CIDR_REGEX)
    result = regex.findall(ip_range)
    if len(result) != 1:
        raise exceptions.ConfigurationError(
            '{0} is not a legal CIDR notation'.format(ip_range))
    subnet, mask = ip_range.split('/')
    return subnet, mask


def _get_subnet_hosts(subnet, mask):
    bin_sub = _ip2long(subnet)
    bin_broadcast = _get_broadcast_long(subnet, mask)
    for address in xrange(bin_sub + 1, bin_broadcast):
        yield _long2ip(address)
