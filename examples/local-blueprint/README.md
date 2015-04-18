## Local Blueprint

[This blueprint](local-blueprint.yaml) allows you to install the cloudify-host-pool-service application on your local machine. <br>
Let see how this is done:

**The pool configuration file is located [here](pool.yaml)**

### Step 1: Initialize

`cfy local init -p local-blueprint.yaml` <br>

This command (as the name suggests) initializes your working directory to work with the given blueprint.
Now, you can run any type of workflows on this blueprint. <br>

### Step 2: Install

Lets run the `install` workflow: <br>

```bash
cfy local execute -w install
2015-04-01 17:39:39 CFY <local> [host_79e11] Creating node
2015-04-01 17:39:39 CFY <local> [host_79e11] Configuring node
2015-04-01 17:39:40 CFY <local> [host_79e11] Starting node
2015-04-01 17:39:40 CFY <local> [host_pool_service_fd5bd] Creating node
2015-04-01 17:39:40 CFY <local> [host_pool_service_fd5bd.create] Sending task 'script_runner.tasks.run'
2015-04-01 17:39:40 CFY <local> [host_pool_service_fd5bd.create] Task started 'script_runner.tasks.run'
2015-04-01 17:39:41 LOG <local> [host_pool_service_fd5bd.create] INFO: Executing: /tmp/tmpFDw8of-create.sh
2015-04-01 17:39:41 LOG <local> [host_pool_service_fd5bd.create] INFO: Creating directory /tmp/cloudify-host-pool-serviceTcJqKm
2015-04-01 17:39:41 LOG <local> [host_pool_service_fd5bd.create] INFO: Creating virtualenv
2015-04-01 17:39:43 LOG <local> [host_pool_service_fd5bd.create] INFO: Installing gunicorn
2015-04-01 17:39:44 LOG <local> [host_pool_service_fd5bd.create] INFO: Installing cloudify-host-pool-service
2015-04-01 17:39:53 LOG <local> [host_pool_service_fd5bd.create] INFO: Execution done (return_code=0): /tmp/tmpFDw8of-create.sh
2015-04-01 17:39:53 CFY <local> [host_pool_service_fd5bd.create] Task succeeded 'script_runner.tasks.run'
2015-04-01 17:39:53 CFY <local> [host_pool_service_fd5bd] Configuring node
2015-04-01 17:39:53 CFY <local> [host_pool_service_fd5bd.configure] Sending task 'script_runner.tasks.run'
2015-04-01 17:39:53 CFY <local> [host_pool_service_fd5bd.configure] Task started 'script_runner.tasks.run'
2015-04-01 17:39:53 LOG <local> [host_pool_service_fd5bd.configure] INFO: Downloading pool configuration file
2015-04-01 17:39:53 LOG <local> [host_pool_service_fd5bd.configure] INFO: Creating service configuration file
2015-04-01 17:39:53 LOG <local> [host_pool_service_fd5bd.configure] INFO: Downloading keyfile: keys/key.pem
2015-04-01 17:39:53 CFY <local> [host_pool_service_fd5bd.configure] Task succeeded 'script_runner.tasks.run'
2015-04-01 17:39:54 CFY <local> [host_pool_service_fd5bd] Starting node
2015-04-01 17:39:54 CFY <local> [host_pool_service_fd5bd.start] Sending task 'script_runner.tasks.run'
2015-04-01 17:39:54 CFY <local> [host_pool_service_fd5bd.start] Task started 'script_runner.tasks.run'
2015-04-01 17:39:54 LOG <local> [host_pool_service_fd5bd.start] INFO: Executing: /tmp/tmpxY_Otx-start.sh
2015-04-01 17:39:54 LOG <local> [host_pool_service_fd5bd.start] INFO: Starting cloudify-host-pool-service with command: gunicorn --workers=5 --pid=/tmp/cloudify-host-pool-serviceTcJqKm/work/gunicorn.pid --log-level=INFO --log-file=/tmp/cloudify-host-pool-serviceTcJqKm/work/gunicorn.log --bind 0.0.0.0:8080 --daemon cloudify_hostpool.rest.service:app
2015-04-01 17:39:55 LOG <local> [host_pool_service_fd5bd.start] INFO: Execution done (return_code=0): /tmp/tmpxY_Otx-start.sh
2015-04-01 17:39:55 CFY <local> [host_pool_service_fd5bd.start] Task succeeded 'script_runner.tasks.run'
2015-04-01 17:39:55 CFY <local> 'install' workflow execution succeeded
```

This command will install all the application components on you local machine.
(don't worry, its all installed under the `tmp` directory by default)<br>
Once its done, you should be able to execute a GET request to [http://localhost:8080/hosts](http://localhost:8080/hosts) and see the result.
<br>


### Step 3: Uninstall

To uninstall the application we run the `uninstall` workflow: <br>

`cfy local execute -w uninstall`
