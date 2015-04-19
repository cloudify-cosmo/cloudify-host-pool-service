#!/bin/bash -e

SOURCE=$(ctx node properties source)

directory=$(ctx node properties directory)

work_directory=${directory}

ctx logger info "Creating directory ${directory}"
mkdir -p ${directory}
cd ${directory}

mkdir -p ${work_directory}

ctx logger info "Installing gunicorn"
pip install gunicorn==18.0
ctx logger info "Installing pyyaml"
pip install pyyaml==3.10
ctx logger info "Installing cloudify-host-pool-service"
pip install ${SOURCE}

ctx instance runtime-properties work_directory ${work_directory}
