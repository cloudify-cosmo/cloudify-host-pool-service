#!/bin/bash -e

SOURCE=$(ctx node properties source)

directory=$(ctx node properties directory)

work_directory=$(ctx node properties working_directory)

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

