#!/bin/bash


_error(){
    echo "$1" 1>&2
    exit 1
}


declare -r _host_pool_dir=$(ctx node properties directory)

[ -d "${_host_pool_dir}" ] || \
    _error "Host pool's directory '${_host_pool_dir}' does not exist!"

ctx logger info "Deleting directory: ${_host_pool_dir}"
rm -rvf "${_host_pool_dir}"
