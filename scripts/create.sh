#!/bin/bash -e

python=$(which python)

echo ${python} > /home/elip/dev/python.txt
SOURCE=$(ctx node properties source)

directory=$(ctx node properties directory)

work_directory=${directory}/work

env_directory=${directory}/env

ctx logger info "Creating directory ${directory}"
mkdir -p ${directory}
cd ${directory}

mkdir -p ${work_directory}

ctx logger info "Creating virtualenv"
virtualenv ${env_directory}
. ${env_directory}/bin/activate

ctx logger info "Installing gunicorn"
pip install gunicorn
ctx logger info "Installing cloudify-host-pool-service"
pip install ${SOURCE}

ctx instance runtime-properties work_directory ${work_directory}
ctx instance runtime-properties env_directory ${env_directory}
