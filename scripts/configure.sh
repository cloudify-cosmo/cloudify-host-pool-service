#!/bin/bash

pool=$(ctx node properties pool)
work_directory=$(ctx instance runtime-properties work_directory)
config_path=${work_directory}/config.json

ctx logger info "Downloading pool configuration file"
ctx download-resource ${pool} "@{\"target_path\": \"${work_directory}/pool.yaml\"}"

ctx logger info "Creating host-pool-service config"
echo "{\"pool\":\"${work_directory}/pool.yaml\"}" >> ${config_path}

ctx instance runtime-properties config_path ${config_path}
