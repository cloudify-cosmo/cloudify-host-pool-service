Cloudify Host Pool Service
==========================

[![Build Status](https://travis-ci.org/cloudify-cosmo/cloudify-host-pool-service.svg?branch=master)](https://travis-ci.org/cloudify-cosmo/cloudify-host-pool-service)

- Usage documentation can be found [Here](http://docs.getcloudify.org/3.3.1/plugins/host-pool/)
- Examples are available [Here](examples)

## Description

The Host Pool Service is a Python 2 RESTful web service built on [flask-restful]
(http://flask-restful-cn.readthedocs.org/en/0.3.5/). The service allows users to
utilize pre-existing hosts that may, or may not, have been previously deployed using
a Cloudify manager.

The service is deployed using a standard Cloudify blueprint and is intended to run
on a separate host from a Cloudify manager. The service is made aware of existing
hosts through RESTful API calls and/or providing a list of hosts as an input during
service deployment.

## API endpoints

 **/hosts** [[GET](#get-hosts), [POST](#post-hosts)]

 **/host/{id}** [[GET](#get-hostid), [PATCH](#patch-hostid), [DELETE](#delete-hostid)]

 **/host/allocate** [[POST](#post-hostallocate)]

  **/host/{id}/deallocate** [[DELETE](#delete-hostiddeallocate)]

## Filters

Filters can be used for both listing hosts ([/hosts GET](#get-hosts)) and allocating hosts
([/host/allocate POST](#post-hostallocate)) and they share the same set of filters.  For instance,
if you want to list all hosts that are Windows hosts, pass the query string ```?os=windows```.
If you've specified tags for your hosts, you may also query them by using ```?tags=tag1,tag2```
but know that searching by tags is an AND operation (all tags must match) and not an OR
operation (any one tag must match). Multiple / array filters are comma separated when passed as
GET query parameters.  When allocating hosts, pass your filters as JSON in the POST data.

Currently, the following filters are accepted:

* __os__ => Filters by OS type (windows or linux)
* __tags__ => Filters by an array of tags assigned to the hosts

## API endpoint details

### [GET] /hosts

Queries the service for all hosts.  Uses [filters](#filters) if provided in the query string.

#### Response
This endpoint returns a list of host details

HTTP/1.1 200 OK
```json
[
    {
        "id": 1,
        "name": "my-linux-server",
        "os": "linux",
        "endpoint": {
            "ip": "192.168.1.100",
            "port": 22,
            "protocol": "ssh"
        },
        "credentials": {
            "username": "ubuntu",
            "password": "Sup3rS3cur3"
        },
        "allocated": false,
        "alive": true
    },
    {
        "id": 2,
        "name": "my-windows-server",
        "os": "linux",
        "endpoint": {
            "ip": "192.168.1.101",
            "port": 5985,
            "protocol": "winrm-http"
        },
        "credentials": {
            "username": "Administrator",
            "key": "-----BEGIN RSA PRIVATE KEY-----...-----END RSA PRIVATE KEY-----"
        },
        "allocated": false,
        "alive": false
    }
]
```

### [POST] /hosts

Adds hosts to the host pool service. Requests should always be a valid JSON array, even if only adding one host.

Similar to how hosts are added during service deployment (using a host pool YAML file), using this endpoint gives you
the ability to specify host defaults.  Also, you may specify a CIDR for the "ip" key to add a block of hosts.  If
a CIDR is specified, each host in the block will have its own entry in the host pool.

**Sending PEM-encoded SSL / TLS keys**

If using the *credentials.key* option, the value must be the key contents in string format.  Using a file path to a
key file is only supported when adding hosts from the host pool YAML file during service deployment.  When sending a
PEM-formatted key via JSON, you must properly encode the string before sending. The easiest way to handle this is to
use the following shell command (replacing *cert-name.pem* with the name of your PEM-encoded file).  The resulting
string is what should be used in the *endpoint.key* field in your request.

```bash
# Convert the PEM-encoded key
KEY_DATA=$(awk 'NF {sub(/\r/, ""); printf "%s\\n",$0;}' hostpool-test.pem)

# Make the API request using the key contents
curl -v -X POST \
-H "Content-Type: application/json" \
-d '{"default": {"os": "linux", "endpoint": {"port": 22, "protocol": "ssh"}}, "hosts":[{"name": "example_host", "endpoint":{"ip": "192.168.1.100"},"credentials":{"username":"centos","key":"'"$KEY_DATA"'"}}]}' \
http://hostpool.example.com:8080/hosts
```

#### Request
```json
{
    "default": {
        "os": "linux",
        "endpoint": {
            "port": 22,
            "protocol": "ssh"
        },
        "credentials": {
            "username": "centos"
        }
    },
    "hosts": [{
        "name": "linux_host",
        "endpoint": {
            "ip": "192.168.1.100/30"
        },
        "credentials": {
            "password": "Sup3rS3cur3"
        }
    }]
}
```

#### Response
This endpoint returns a list of created host IDs for use with **/host/{id}** [[GET](#get-hostid)]

HTTP/1.1 201 CREATED
```json
[1, 2, 3, 4]
```

### [GET] /host/{id}

Retrieves details about a single host by host ID

#### Response
This endpoint returns the details of a host

HTTP/1.1 200 OK
```json

{
    "id": 1,
    "name": "linux_host_1",
    "os": "linux",
    "endpoint": {
        "ip": "192.168.1.100",
        "port": 22,
        "protocol": "ssh"
    },
    "credentials": {
        "username": "centos",
        "password": "Sup3rS3cur3"
    },
    "allocated": false,
    "alive": false
}
```

### [PATCH] /host/{id}

Applies a partial update on the host.  Useful for performing tasks such as updating a password or
changing an endpoint port.

#### Request
```json
{
    "credentials": {
        "password": "Som3Oth3rP@ssword"
    }
}
```

#### Response
This endpoint returns the ID of an updated host for use with **/host/{id}** [[GET](#get-hostid)]

HTTP/1.1 200 OK
```json
1
```

### [DELETE] /host/{id}

Removes a host from the service

#### Request
```bash
curl -X DELETE http://hostpool.example.com:8080/host/1
```

#### Response
HTTP/1.1 204 NO CONTENT

### [POST] /host/allocate

Allocates a host from the pool for use by the user. This endpoint will check if the hosts'
endpoint is "alive" (able to be connected to) or not and will mark the host as "allocated" before
returning the host details to the user.  Uses [filters](#filters) if provided as JSON data.

An "os" can be specified but is not required.

#### Request
```json
{
    "os": "linux",
    "tags": ["large"]
}
```

#### Response
This endpoint returns the details of a host

HTTP/1.1 200 OK
```json
{
    "id": 1,
    "name": "linux_host_1",
    "os": "linux",
    "endpoint": {
        "ip": "192.168.1.100",
        "port": 22,
        "protocol": "ssh"
    },
    "credentials": {
        "username": "centos",
        "password": "Sup3rS3cur3"
    },
    "tags": ["large", "ubuntu"],
    "allocated": true,
    "alive": true
}
```

### [DELETE] /host/{id}/deallocate

Deallocates a host from the user to the host pool for reuse

#### Request
```bash
curl -X DELETE http://hostpool.example.com:8080/host/1/deallocate
```

#### Response
HTTP/1.1 204 NO CONTENT
