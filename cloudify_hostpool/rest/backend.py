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
    cloudify_hostpool.rest.backend
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RESTful service backend methods
'''

# pylint: disable=R0911

import socket
import logging
import filelock
from copy import deepcopy
from collections import Mapping

# Used for IP / CIDR routines
from netaddr import IPNetwork
from netaddr.core import AddrFormatError

from .. import constants
from .. import exceptions
from .._compat import text_type
from ..storage.tinydb_nosql import Database

# we currently don't expose these in the configuration because its somewhat
# internal. perhaps at a later time we can have this configurable, at which
# point we need to define the semantics of how to initialize the components.
FLOCK = filelock.FileLock('host-pool-backend.lock')

# HostAlchemist
# - Converts user-provided host entries into a consumable structure
# HostReconciler
# - Handles any host entry duplication cases


class HostAlchemist(object):
    '''Converts user-provided host entries into a consumable structure'''
    def __init__(self, config):
        self.config = config

    def parse(self):
        '''Performs the config-to-hosts analysis and conversion'''
        hosts = []
        defaults = self.get_config_defaults()
        # Fix defaults
        if isinstance(defaults, dict):
            if defaults.get('platform'):
                del defaults['platform']
            if isinstance(defaults.get('endpoint'), dict) and \
               defaults.get('endpoint').get('ip'):
                del defaults['endpoint']['ip']
        # Validate the defaults
        self.validate_defaults(defaults)
        # Build an extended list of hosts
        for host in self.get_config_hosts():
            # Merge defaults into hosts
            self.impose_defaults(host, defaults)
            # Soft-validate the base host
            self.validate_host(host, check_ip_range=False)
            hip = IPNetwork(host['endpoint']['ip'])
            hname = host['name']
            if len(list(hip)) > 1:
                # This is an IP address range endpoint
                for idx, sip in enumerate(list(hip)):
                    shost = deepcopy(host)
                    shost['endpoint']['ip'] = text_type(sip)
                    if hname:
                        shost['name'] = '{0}_{1}'.format(hname, idx)
                    hosts.append(shost)
            else:
                # This is a single IP endpoint
                host['endpoint']['ip'] = text_type(list(hip)[0])
                hosts.append(host)
        # Post-process hosts
        for host in hosts:
            # Add in backend details
            host['allocated'] = False
            host['alive'] = False
            # Validate the extended hosts list
            self.validate_host(host)
        return hosts

    def get_config_defaults(self):
        '''Returns the default config'''
        return self.config.get('default', {})

    def get_config_hosts(self):
        '''Returns the hosts config'''
        return self.config.get('hosts', [])

    @staticmethod
    def validate_defaults(defaults):
        '''Validates default data'''
        if not defaults:
            return
        if not isinstance(defaults, dict):
            raise exceptions.ConfigurationError(
                'Defaults must be a valid JSON Object')
        if defaults.get('platform'):
            raise exceptions.ConfigurationError(
                'Default "platform" is not allowed')
        if defaults.get('endpoint') and \
           not isinstance(defaults.get('endpoint'), dict):
            raise exceptions.ConfigurationError(
                'Default "endpoint" must be a valid JSON Object')
        if defaults.get('credentials') and \
           not isinstance(defaults.get('credentials'), dict):
            raise exceptions.ConfigurationError(
                'Default "credentials" must be a valid JSON Object')
        if defaults.get('endpoint') and \
           defaults['endpoint'].get('ip'):
            raise exceptions.ConfigurationError(
                'Default "endpoint.ip" is not allowed')
        # Validate tags
        if not isinstance(defaults.get('tags', list()), list):
            raise exceptions.ConfigurationError(
                'Default "tags" must be a valid JSON Array')

    @staticmethod
    def validate_host_endpoint(endpoint, check_ip_range=True):
        '''Validates a host endpoint'''
        if 'ip' not in endpoint or \
           not isinstance(endpoint['ip'], text_type):
            raise exceptions.ConfigurationError(
                'Host endpoint must have a valid "ip" key')
        if 'port' not in endpoint or \
           not isinstance(endpoint['port'], int):
            raise exceptions.ConfigurationError(
                'Host endpoint must have a valid "port" key')
        if 'protocol' not in endpoint or \
           not isinstance(endpoint['protocol'], text_type):
            raise exceptions.ConfigurationError(
                'Host endpoint must have a valid "protocol" key')
        try:
            _ip = IPNetwork(endpoint['ip'])
            if check_ip_range:
                if len(list(_ip)) != 1:
                    raise exceptions.ConfigurationError(
                        'IP address ranges are not valid per host')
        except AddrFormatError:
            raise exceptions.ConfigurationError(
                'IP address "{0}" is not in valid CIDR format'.format(
                    endpoint['ip']))

    @staticmethod
    def validate_host_credentials(credentials):
        '''Validates a hosts' credentials'''
        if not credentials:
            raise exceptions.ConfigurationError(
                'No credentials set for host')
        if not isinstance(credentials, dict):
            raise exceptions.ConfigurationError(
                'Host credentials must be a valid JSON object')
        if not credentials.get('username') or \
           not isinstance(credentials.get('username'), text_type):
            raise exceptions.ConfigurationError(
                'No username set for host')
        if credentials.get('password') and \
           not isinstance(credentials.get('password'), text_type):
            raise exceptions.ConfigurationError(
                'Invalid, non-string password set for host')
        if credentials.get('key') and \
           not isinstance(credentials.get('key'), text_type):
            raise exceptions.ConfigurationError(
                'Invalid, non-string key set for host')

    def validate_host(self, host, check_ip_range=True):
        '''Validates host data'''
        # Validate OS type
        if not isinstance(host['os'], text_type) or \
           host['os'] not in ['windows', 'linux']:
            raise exceptions.ConfigurationError(
                'Invalid or missing OS for host')
        # Validate endpoint
        if not host.get('endpoint'):
            raise exceptions.ConfigurationError(
                'No endpoint set for host')
        if not isinstance(host.get('endpoint'), dict):
            raise exceptions.ConfigurationError(
                'Host endpoint must be a JSON Object')
        self.validate_host_endpoint(host.get('endpoint'),
                                    check_ip_range=check_ip_range)
        # Validate credentials
        self.validate_host_credentials(host.get('credentials'))
        # Validate tags
        if not isinstance(host.get('tags', list()), list):
            raise exceptions.ConfigurationError(
                'Invalid, non-list tags set for host')

    def impose_defaults(self, host, defaults):
        '''Adds default configuration to hosts'''
        # Add default name, OS type, etc...
        self.impose_default_base(host, defaults)
        # Add default endpoints
        self.impose_default_endpoints(host, defaults)
        # Add default credentials
        self.impose_default_credentials(host, defaults)

    @staticmethod
    def impose_default_base(host, defaults):
        '''Adds default base information to a host'''
        host['name'] = host.get('name') or defaults.get('name')
        host['os'] = host.get('os') or defaults.get('os')
        # Set tags. If tags are malformed, ConfigurationError is raised later
        if not host.get('tags') or isinstance(host.get('tags'), list):
            host['tags'] = list(set(
                host.get('tags', list()) + defaults.get('tags', list())))

    @staticmethod
    def impose_default_credentials(host, defaults):
        '''Adds default credentials information to a host'''
        if defaults.get('credentials'):
            if host.get('credentials'):
                creds = host.get('credentials')
                creds_default = deepcopy(defaults.get('credentials'))
                creds_default.update(creds)
                creds.update(creds_default)
            else:
                host['credentials'] = defaults.get('credentials')

    @staticmethod
    def impose_default_endpoints(host, defaults):
        '''Adds default endpoint information to a host'''
        if defaults.get('endpoint'):
            if host.get('endpoint'):
                enp = host.get('endpoint')
                enp_default = deepcopy(defaults.get('endpoint'))
                enp_default.update(enp)
                enp.update(enp_default)
            else:
                host['endpoint'] = [defaults.get('endpoint')]


def dict_update(orig, updates):
    '''Recursively merges two objects'''
    for key, val in updates.items():
        if isinstance(val, Mapping):
            orig[key] = dict_update(orig.get(key, {}), val)
        else:
            orig[key] = updates[key]
    return orig


class RestBackend(object):
    '''RESTful service backend class'''
    def __init__(self, logger=None, reset_storage=False, storage=None):
        if not logger:
            logger = logging.getLogger('hostpool.rest.backend')
        self.logger = logger.getChild('backend')
        self.logger.setLevel(logging.DEBUG)
        self.storage = Database(storage)
        if reset_storage:
            with FLOCK.acquire(timeout=10):
                self.storage.init_data()

    def list_hosts(self, filters=None):
        '''Get an iterable of all hosts'''
        self.logger.debug('backend.list_hosts()')
        return [x for x in self.storage.get_hosts()
                if self.check_host_by_filters(x, filters)]

    def add_hosts(self, config):
        '''Adds hosts to the host pool'''
        self.logger.debug('backend.add_hosts({0})'.format(config))
        if not isinstance(config, dict) or \
           not config.get('hosts'):
            raise exceptions.UnexpectedData('Empty hosts object')
        hosts = HostAlchemist(config).parse()
        return self.storage.add_hosts(hosts)

    def remove_host(self, host_id):
        '''Remove a host from the host pool'''
        self.logger.debug('backend.remove_host({0})'.format(host_id))
        if not host_id or not isinstance(host_id, int):
            raise exceptions.HostNotFoundException(host_id)
        h_id = self.storage.remove_host(host_id)
        if not h_id:
            raise exceptions.HostNotFoundException(host_id)
        return h_id

    def update_host(self, host_id, updates):
        '''Updates a host in the host pool'''
        self.logger.debug('backend.update_host({0})'.format(host_id))
        if not host_id or not isinstance(host_id, int):
            raise exceptions.HostNotFoundException(host_id)
        if not isinstance(updates, dict):
            raise exceptions.UnexpectedData('Updates must be a JSON object')
        orig = self.storage.get_host(host_id)
        if not orig:
            raise exceptions.HostNotFoundException(host_id)
        updated = dict_update(orig, updates)
        h_id = self.storage.update_host(host_id, updated)
        if not h_id:
            raise exceptions.HostNotFoundException(host_id)
        return h_id

    def check_host_by_filters(self, host, filters):
        '''Check if a host matches a set of filters'''
        # Basic validation
        if not filters or not isinstance(filters, dict):
            self.logger.warn('No filters specified')
            return True
        if not host:
            self.logger.warn('No host specified')
            return False
        # Check filters using a True fall-through
        # Check OS
        if filters.get('os'):
            if not isinstance(filters.get('os'), text_type):
                self.logger.warn('Invalid, non-string requested OS provided')
                return False
            if filters.get('os').lower() != host.get('os', '').lower():
                self.logger.warn('Host does not match all filters '
                                 '(os={0})'.format(filters.get('os').lower()))
                return False
        # Check tags (AND method)
        if filters.get('tags'):
            if not isinstance(filters.get('tags'), list):
                self.logger.warn('Invalid, non-list requested tags provided')
                return False
            for tag in filters.get('tags'):
                if tag not in host.get('tags', list()):
                    self.logger.warn('Host does not match all filters '
                                     '(tags={0})'.format(filters.get('tags')))
                    return False
        return True

    def acquire_host(self, filters=None):
        '''Acquire a host, mark it taken'''
        self.logger.debug('backend.acquire_host({0})'.format(filters))
        # Configure a file lock
        lock = filelock.FileLock('host_acquire.lck')
        for host in self.get_unallocated_hosts():
            # Get host ID
            host_id = host[constants.HOST_ID_KEY]
            # Enforce any user-defined requests
            if self.check_host_by_filters(host, filters) and \
               self.host_port_scan(host['endpoint']):
                # Ensure the host is still free
                with lock.acquire():
                    _host = self.storage.get_host(host_id)
                    if not _host['allocated']:
                        self.storage.update_host(host_id,
                                                 {'allocated': True})
                        return self.storage.get_host(host_id)
        # We didn't manage to acquire any host
        raise exceptions.NoHostAvailableException()

    def release_host(self, host_id):
        '''Release a host, free it'''
        if not host_id or not isinstance(host_id, int):
            raise exceptions.HostNotFoundException(host_id)
        # Get a file lock
        lock = filelock.FileLock('host_acquire.lck')
        with lock.acquire():
            self.storage.update_host(host_id, {'allocated': False})
            return self.storage.get_host(host_id)

    def get_host(self, host_id):
        '''Gets a host + key data'''
        self.logger.debug('backend.get_host({0})'.format(host_id))
        if not host_id or not isinstance(host_id, int):
            raise exceptions.HostNotFoundException(host_id)
        # Get a file lock
        lock = filelock.FileLock('host_acquire.lck')
        with lock.acquire():
            host = self.storage.get_host(host_id)
            if not host:
                raise exceptions.HostNotFoundException(host_id)
            return host

    def get_unallocated_hosts(self):
        '''Get free hosts'''
        return [x for x in self.list_hosts() if not x['allocated']]

    def host_port_scan(self, endpoint):
        '''Scans a TCP port'''
        # Basic validation
        if not endpoint or not endpoint.get('ip') or not endpoint.get('port'):
            self.logger.error('Invalid endpoint specified')
            return False

        # Creates a TCP socket
        sock = socket.socket()
        sock.settimeout(1)
        self.logger.info('Testing endpoint tcp://{0}:{1}'.format(
            endpoint['ip'], endpoint['port']))
        try:
            sock.connect((endpoint['ip'], endpoint['port']))
            sock.close()
            self.logger.info('Successfully connected to '
                             'endpoint tcp://{0}:{1}'.format(
                                 endpoint['ip'], endpoint['port']))
            return True
        except socket.error as exc:
            self.logger.warn('Error connecting to endpoint tcp://{0}:{1}. '
                             'Exception: {2}'.format(
                                 endpoint['ip'], endpoint['port'], exc))
            return False
