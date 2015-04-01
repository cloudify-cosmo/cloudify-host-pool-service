#!/bin/bash

SOURCE=$(ctx node properties source)

directory=$(ctx node properties directory)
work_directory=${directory}/work
env_directory=${directory}/env

sudo apt-get install python-dev

mkdir -p ${directory}
cd ${directory}

mkdir -p ${work_directory}

virtualenv ${env_directory}
. ${env_directory}/bin/active

pip install ${SOURCE}
pip install gunicorn

ctx instance runtime-properties work_directory ${work_directory}
ctx instance runtime-properties env_directory ${env_directory}