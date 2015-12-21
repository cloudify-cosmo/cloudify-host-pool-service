########
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
import httplib
import yaml

from flask import Flask
from flask import request
from flask import jsonify
from flask_restful import Api

from cloudify_hostpool import exceptions
from cloudify_hostpool import utils
from cloudify_hostpool.rest import backend as rest_backend
from cloudify_hostpool.rest import config


app, backend = None, None


def setup():

    global app, backend

    # initialize flask application
    app = Flask(__name__)
    Api(app)

    # load application configuration file is exists
    config_file_path = os.environ.get('HOST_POOL_SERVICE_CONFIG_PATH')
    if config_file_path:
        utils.write_to_log('service.setup', "config_file_path {0}".format(config_file_path))
        with open(config_file_path) as f:
            yaml_conf = yaml.load(f.read())
            config.configure(yaml_conf)
        utils.write_to_log('service.setup', "config_file_path {0} after configure".format(config_file_path))
    else:
        utils.write_to_log('service.setup', "Failed loading application: " \
              "HOST_POOL_SERVICE_CONFIG_PATH environment variable is not defined. " \
              "Use this variable to point to the application configuration file ")
        raise exceptions.ConfigurationError(
            'Failed loading application: '
            'HOST_POOL_SERVICE_CONFIG_PATH environment '
            'variable is not defined. Use this variable to '
            'point to the application configuration file ')

    # initialize application backend
    backend = rest_backend.RestBackend(pool=config.get().pool)


def reset_backend():
    global app, backend
    # initialize application backend
    backend = rest_backend.RestBackend(pool=config.get().pool)

setup()


@app.errorhandler(exceptions.HostPoolHTTPException)
def handle_errors(error):
    response = jsonify(error.to_dict())
    response.status_code = error.get_code()
    return response


@app.route('/hosts', methods=['GET'])
def list_hosts():

    """
    List allocated hosts
    """

    value_of_arg_all_key = utils.get_arg_value('all', arg_value='')
    get_all_hosts = value_of_arg_all_key.lower() in ('yes', 'true')
    hosts = backend.list_hosts(get_all_hosts)
    utils.write_to_log('service.setup', "list_hosts is {0}".format(str(hosts)))
    return jsonify(hosts=hosts), httplib.OK


@app.route('/log', methods=['GET'])
def display_log_file():

    """
    Displays the log file of this service
    """

    file_content = utils.get_log_file_content()
    return file_content, httplib.OK

@app.route('/hosts', methods=['POST'])
def acquire_host():

    """
    Acquire(allocate) the host
    """

    host = backend.acquire_host()
    return jsonify(host), httplib.CREATED


@app.route('/hosts/<host_id>', methods=['DELETE'])
def release_host(host_id):

    """
    Release the host with the given host_id
    """

    host = backend.release_host(host_id)
    return jsonify(host), httplib.OK


@app.route('/hosts/<host_id>', methods=['GET'])
def get_host(host_id):

    """
    Get the details of the host with the given host_id
    """

    host = backend.get_host(host_id)
    return jsonify(host), httplib.OK


if __name__ == '__main__':
    app.run()
