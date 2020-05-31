## Local Blueprint

[This blueprint](local-blueprint.yaml) allows you to install the cloudify-host-pool-service application on your local machine. <br>
Let see how this is done:

**The pool configuration file is located [here](pool.yaml)**

### Step 1: Initialize

`cfy profiles use local`

`cfy init local-blueprint.yaml` <br>

This command (as the name suggests) initializes your working directory to work with the given blueprint.
Now, you can run any type of workflows on this blueprint. <br>

### Step 2: Install

Lets run the `install` workflow: <br>

```bash
cfy executions start -b local-blueprint install
2017-05-10 15:55:59.094  CFY <local-blueprint> Starting 'install' workflow execution
2017-05-10 15:55:59.213  CFY <local-blueprint> [host_flp0ik] Creating node
2017-05-10 15:55:59.641  CFY <local-blueprint> [host_flp0ik] Configuring node
2017-05-10 15:56:00.021  CFY <local-blueprint> [host_flp0ik] Starting node
2017-05-10 15:56:01.017  CFY <local-blueprint> [host_pool_service_52hipx] Creating node
2017-05-10 15:56:01.106  CFY <local-blueprint> [host_pool_service_52hipx.create] Sending task 'script_runner.tasks.run'
2017-05-10 15:56:01.131  CFY <local-blueprint> [host_pool_service_52hipx.create] Task started 'script_runner.tasks.run'
2017-05-10 15:56:01.313  LOG <local-blueprint> [host_pool_service_52hipx.create] INFO: Creating working directory: "/tmp"
2017-05-10 15:56:01.313  LOG <local-blueprint> [host_pool_service_52hipx.create] INFO: Installing required Python packages
2017-05-10 15:56:01.313  LOG <local-blueprint> [host_pool_service_52hipx.create] INFO: Installing Python package "gunicorn==19.4.5"
2017-05-10 15:56:01.908  LOG <local-blueprint> [host_pool_service_52hipx.create] INFO: Installing Python package "pyyaml==3.11"
2017-05-10 15:56:02.585  LOG <local-blueprint> [host_pool_service_52hipx.create] INFO: Installing Python package "https://github.com/cloudify-cosmo/cloudify-host-pool-service/archive/1.1.zip"
2017-05-10 15:56:05.472  LOG <local-blueprint> [host_pool_service_52hipx.create] INFO: Setting runtime_property "working_directory" to "/tmp"
2017-05-10 15:56:05.473  CFY <local-blueprint> [host_pool_service_52hipx.create] Task succeeded 'script_runner.tasks.run'
2017-05-10 15:56:05.751  CFY <local-blueprint> [host_pool_service_52hipx] Configuring node
2017-05-10 15:56:05.818  CFY <local-blueprint> [host_pool_service_52hipx.configure] Sending task 'script_runner.tasks.run'
2017-05-10 15:56:05.865  CFY <local-blueprint> [host_pool_service_52hipx.configure] Task started 'script_runner.tasks.run'
2017-05-10 15:56:06.046  LOG <local-blueprint> [host_pool_service_52hipx.configure] INFO: Loading Host-Pool seed hosts
2017-05-10 15:56:06.051  LOG <local-blueprint> [host_pool_service_52hipx.configure] INFO: Converting host key files from blueprint
2017-05-10 15:56:06.055  CFY <local-blueprint> [host_pool_service_52hipx.configure] Task succeeded 'script_runner.tasks.run'
2017-05-10 15:56:06.433  CFY <local-blueprint> [host_pool_service_52hipx] Starting node
2017-05-10 15:56:06.520  CFY <local-blueprint> [host_pool_service_52hipx.start] Sending task 'script_runner.tasks.run'
2017-05-10 15:56:06.547  CFY <local-blueprint> [host_pool_service_52hipx.start] Task started 'script_runner.tasks.run'
2017-05-10 15:56:06.725  LOG <local-blueprint> [host_pool_service_52hipx.start] INFO: Downloading Host-Pool service init script
2017-05-10 15:56:06.743  LOG <local-blueprint> [host_pool_service_52hipx.start] INFO: (sudo) Starting the Host-Pool service
Starting Cloudify Host-Pool service...
Cloudify Host-Pool service started with pid 12525
2017-05-10 15:56:09.030  LOG <local-blueprint> [host_pool_service_52hipx.start] INFO: (sudo) Enabling the Host-Pool service on boot
 System start/stop links for /etc/init.d/cloudify-hostpool already exist.
2017-05-10 15:56:09.052  LOG <local-blueprint> [host_pool_service_52hipx.start] INFO: [Attempt 0/20] Liveness detection check
2017-05-10 15:56:09.107  LOG <local-blueprint> [host_pool_service_52hipx.start] INFO: Host-Pool service is alive
2017-05-10 15:56:09.107  LOG <local-blueprint> [host_pool_service_52hipx.start] INFO: Installing seed hosts data
2017-05-10 15:56:09.111  CFY <local-blueprint> [host_pool_service_52hipx.start] Task succeeded 'script_runner.tasks.run'
2017-05-10 15:56:09.527  CFY <local-blueprint> 'install' workflow execution succeeded
```

This command will install all the application components on you local machine.
(don't worry, its all installed under the `tmp` directory by default)<br>
Once its done, you should be able to execute a GET request to [http://localhost:8080/hosts](http://localhost:8080/hosts) and see the result.
**Note that the result should be an empty array, because this request only
shows allocated hosts.**
<br>


### Step 3: Uninstall

To uninstall the application we run the `uninstall` workflow: <br>

`cfy executions start -b local-blueprint uninstall`
