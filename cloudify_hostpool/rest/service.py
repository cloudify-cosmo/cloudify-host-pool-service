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
    cloudify_hostpool.rest.service
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RESTful service endpoints and initialization
'''

# pylint: disable=C0103
# pylint: disable=W0603

import httplib
import logging

from flask import Flask, request
from flask_restful import Api, Resource

from cloudify_hostpool.rest import backend as rest_backend

# Globals
app, api, backend = None, None, None


def setup():
    '''Service entry point'''
    global app, backend
    # initialize flask application
    app = Flask(__name__)
    # configure Flask to Gunicorn logging
    gunicorn_handlers = logging.getLogger('gunicorn.error').handlers
    app.logger.handlers.extend(gunicorn_handlers)
    app.logger.info('Flask, Gunicorn logging enabled')
    # initialize application backend
    backend = rest_backend.RestBackend(logger=app.logger)


def reset_backend():
    '''Initialize application backend'''
    global backend
    app.logger.info('Resetting API service database data')
    backend = rest_backend.RestBackend(logger=app.logger,
                                       reset_storage=True)


setup()


class Service(Api):
    '''Central API service handler'''
    def handle_error(self, e):
        '''Handle service-wide exceptions'''
        app.logger.error('API exception caught: {0}::{1}'.format(
            type(e), e))
        if hasattr(e, 'status_code'):
            app.logger.error('Exception.status_code: {0}'.format(
                e.status_code))
            return self.make_response({
                'message': str(e)
            }, e.status_code)
        return super(Service, self).handle_error(e)


api = Service(app)


class Host(Resource):
    '''Host object handling'''
    @staticmethod
    def get(host_id):
        '''Get the details of the host with the given host_id'''
        app.logger.debug('GET /host/{0}'.format(host_id))
        host = backend.get_host(host_id)
        return host, httplib.OK

    @staticmethod
    def delete(host_id):
        '''Removes a host from the host pool'''
        app.logger.debug('DELETE /host/{0}'.format(host_id))
        backend.remove_host(host_id)
        return {}, httplib.NO_CONTENT

    @staticmethod
    def patch(host_id):
        '''Updates a host in the host pool'''
        data = request.get_json() or dict()
        app.logger.debug('PATCH /host/{0}, data="{1}"'.format(
            host_id, data))
        host = backend.update_host(host_id, data)
        return host, httplib.OK


class HostList(Resource):
    '''Endpoint for host lists'''
    @staticmethod
    def get():
        '''Get the details of the host with the given host_id'''
        app.logger.debug('GET /hosts')
        hosts = backend.list_hosts()
        return hosts, httplib.OK

    @staticmethod
    def post():
        '''Adds host(s) to the host pool'''
        hosts = request.get_json()
        app.logger.debug('POST /hosts, data="{0}"'.format(hosts))
        if not hosts:
            return 'Data must be a valid JSON array', httplib.BAD_REQUEST
        ret = backend.add_hosts(hosts)
        return ret, httplib.CREATED


class HostAllocate(Resource):
    '''Endpoint to acquire a host from the pool'''
    @staticmethod
    def post():
        '''Allocates a host from the pool'''
        data = request.get_json() or dict()
        app.logger.debug('POST /host/allocate, data="{0}"'.format(data))
        host = backend.acquire_host(requested_os=data.get('os'))
        return host, httplib.OK


class HostDeallocate(Resource):
    '''Endpoing to release a host to the pool'''
    @staticmethod
    def delete(host_id):
        '''Deallocates a host from the pool'''
        app.logger.debug('DELETE /host/{0}/deallocate'.format(host_id))
        host = backend.release_host(host_id)
        return host, httplib.NO_CONTENT


# Map the endpoints to classes
api.add_resource(Host, '/host/<int:host_id>')
api.add_resource(HostList, '/hosts')
api.add_resource(HostAllocate, '/host/allocate')
api.add_resource(HostDeallocate, '/host/<int:host_id>/deallocate')

if __name__ == '__main__':
    app.run()
