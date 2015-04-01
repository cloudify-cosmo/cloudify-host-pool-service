#!/bin/bash

env_directory=$(ctx instance runtime-properties env_directory)
work_directory=$(ctx instance runtime-properties work_directory)
config_path=$(ctx instance runtime-properties config_path)
port=$(ctx node properties port)

cd ${work_directory}
. ${env_directory}/bin/activate
export HOST_POOL_SERVICE_CONFIG_PATH=${config_path}
gunicorn --workers=5 --pid=${work_directory}/gunicorn.pid --log-level=INFO --log-file=${work_directory}/gunicorn.log --bind 0.0.0.0:${port} --daemon cloudify_hostpool.rest.service:app

ctx instance runtime-properties pid_file ${work_directory}/gunicorn.pid