#!/bin/bash

function get_response_code() {

    port=$1

    set +e

    curl_cmd=$(which curl)
    wget_cmd=$(which wget)

    if [[ ! -z ${curl_cmd} ]]; then
        response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${port}/hosts)
    elif [[ ! -z ${wget_cmd} ]]; then
        response_code=$(wget --spider -S "http://localhost:${port}/hosts" 2>&1 | grep "HTTP/" | awk '{print $2}' | tail -1)
    else
        ctx logger error "Failed to retrieve response code from http://localhost:${port}/hosts --> Neither 'cURL' nor 'wget' were found
         on the system"
        exit 1;
    fi

    set -e

    echo ${response_code}

}


function wait_for_server() {

    port=$1
    server_name=$2

    started=false

    ctx logger info "Running ${server_name} liveness detection on port ${port}"

    for i in $(seq 1 5)
    do
        response_code=$(get_response_code ${port})
        ctx logger info "[GET] http://localhost:${port}/hosts ${response_code}"
        if [ ${response_code} -eq 200 ] ; then
            started=true
            break
        else
            ctx logger info "${server_name} has not started. waiting..."
            sleep 1
        fi
    done
    if [ ${started} = false ]; then
        ctx logger error "${server_name} failed to start: $(cat ${work_directory}/gunicorn.log)"
        exit 1
    fi
}


work_directory=$(ctx instance runtime-properties work_directory)
config_path=$(ctx instance runtime-properties config_path)
port=$(ctx node properties port)

cd ${work_directory}
export HOST_POOL_SERVICE_CONFIG_PATH=${config_path}
command="gunicorn --workers=5 --pid=${work_directory}/gunicorn.pid --log-level=INFO --log-file=${work_directory}/gunicorn.log --bind 0.0.0.0:${port} --daemon cloudify_hostpool.rest.service:app"
ctx logger info "Starting cloudify-host-pool-service with command: ${command}"
${command}

wait_for_server ${port} 'Host-Pool-Service'

host_ip=$(ctx instance host-ip)

ctx instance runtime-properties pid_file ${work_directory}/gunicorn.pid
ctx instance runtime-properties private_endpoint "${host_ip}:${port}"