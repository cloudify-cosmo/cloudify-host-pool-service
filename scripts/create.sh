#!/bin/bash -e

SOURCE=$(ctx node properties source)

work_directory=$(ctx node properties working_directory)

ctx logger info "Creating directory ${work_directory}"
mkdir -p ${work_directory}
cd ${work_directory}

target_wagon=hostpoolservice.wgn
ctx logger info "Downloading the wagon ${SOURCE} to ${target_wagon}..."
wget -O ${target_wagon} ${SOURCE}

DPLID=$(ctx deployment id)
currVenv=/root/${DPLID}/env
ctx logger info "deployment_id = ${DPLID}, virtual env is ${currVenv}"
wagonPath=${currVenv}/bin/wagon
ctx logger info "wagonPath is ${wagonPath}"
${wagonPath} install -s ${target_wagon} -e ${currVenv}
ctx logger info "End of create"