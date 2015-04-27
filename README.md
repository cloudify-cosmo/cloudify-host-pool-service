Cloudify Host Pool Service
==========================

[![Build Status](https://travis-ci.org/cloudify-cosmo/cloudify-host-pool-service.svg?branch=master)](https://travis-ci.org/cloudify-cosmo/cloudify-host-pool-service)

- Usage documentation can be found [Here](http://getcloudify.org/guide/3.2/plugin-host-pool.html#host-pool-service)
- Examples are available [Here](examples)

## Description

The service is a python web service based on [flask-restful]
(https://flask-restful.readthedocs.org/en/0.3.2/) that exposes a REST API to
 be consumed by clients who are interested in using hosts from a pool of
 pre-existing hosts.

### [GET] /hosts

Queries the service for all **allocated** hosts.

```json
{
  "hosts": [
    {
      "host_id": "ed11c216-0bd5-4beb-94e1-6d782acb365e",
      "host": "192.168.9.11",
      "public_address": "15.16.17.18",
      "auth": {
        "username": "username",
        "password": "password",
        "keyfile": null
      },
      "port": 22
    }
  ]
}
```

### [GET] /hosts/<host_id>

Get information on a specific host. The host id generated while acquiring
this host must be passed.

```json
{
  "host_id": "ed11c216-0bd5-4beb-94e1-6d782acb365e",
  "host": "192.168.9.11",
  "public_address": "15.16.17.18",
  "auth": {
    "username": "username",
    "password": "password",
    "keyfile": null
  },
  "port": 22
}
```

### [POST] /hosts

Acquire a host.

```json
{
  "host_id": "ed11c216-0bd5-4beb-94e1-6d782acb365e",
  "host": "192.168.9.11",
  "public_address": "15.16.17.18",
  "auth": {
    "username": "username",
    "password": "password",
    "keyfile": null
  },
  "port": 22
}
```

### [DELETE] /hosts/<host_id>

Release a host by its id. response is the deleted host

```json
{
  "host_id": "ed11c216-0bd5-4beb-94e1-6d782acb365e",
  "host": "192.168.9.11",
  "public_address": "15.16.17.18",
  "auth": {
    "username": "username",
    "password": "password",
    "keyfile": null
  },
  "port": 22
}
```

