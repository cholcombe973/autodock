Autodock
========
All the deliciousness of a crazy KFC combination sandwich...none of the shame.  

Autodock is a docker automation tool. This tool will help you spin up docker containers faster than ever!  
It automatically sorts servers in your Docker cluster by lowest load.  It then distributes the containers you want to create among them.  
After bootstrapping the containers with Paramiko and Salt it saves this information to the ETCD cluster.  


Autodock was designed to use saltstack and etcd for configuration management and replication.

## Getting Started
Autodock is currently only tested on Ubuntu 13.04.  
Testing and pull requests for other platforms are welcome.  
Autodock has a few requirements that need to be in place before it will function properly.  
* Docker 0.6+.  0.7.2+ highly encouraged due to bugs
* [Saltstack](http://docs.saltstack.com/topics/index.html)  
* Python 2.7+
* [Python Paramiko](https://github.com/paramiko/paramiko) to ssh into containers
* [Etcd](https://github.com/coreos/etcd)
* GoLang, so Etcd can function
* A docker base container

### Usage

1. Log into a salt master node. Setting up [Multi Master](http://docs.saltstack.com/topics/tutorials/multimaster.html) is highly encouraged!

Synopsis
```
autodock {list,verify,backup,create}  
Autodock is split into several subcommands.  Each subcommand has its own options:  

list usage:   autodock list [-h] -u USERNAME 
backup usage: autodock backup [-h] -u USERNAME -f FORMATION
create usage: autodock create [-h] -u USERNAME -f FORMATION [-n NUMBER]
                       [-c CPU_SHARES] [-r RAM] -s HOSTNAME_SCHEME
                       [-p PORT_LIST] [-z HOST_SERVER] [-d DELETE]
                       [-v VOLUME_LIST]

example: autodock create -f owncloud -n 3 -c 100 -r 100M -h clwebdev
Which will cause it to spin up three containers with a formation name of owncloud, 10% of the cpu allocated, 
100MB of ram and a hostname of clweb001, clweb002, clweb003, and register this formation with the nginx 
load balancers. The formation just means clweb001-003 all serve the owncloud web application. Once the 
container starts up I'll ssh into each container, bootstrap salt and setup a salt-call cron job to setup 
the container. All we need is to have a salt top.sls matcher in place to apply whatever changes we want. 
Following our example it would be install nginx, install uwsgi, hg pull the latest from the repo, setup 
the nginx hosts file and start both nginx and uwsgi.
```
### Description
list options:
* -u, -username
    - The username who owns this formation.

backup options:
* -u, -username
    - The username who owns this formation.
* -f, --formation
    - The formation to backup

create options:
* -u, --username
    - The username who owns this formation. Each user will be able to see only their containers.
* -f, --formation
    - A Formation is a set of infrastructure used to host Applications. Each formation includes Nodes that provide different services to the formation.
* -n, --number
    - The number of containers to build, ex: 1
* -c, --cpu_shares
    - A percentage of the cpu that the container is allowed to use. CPU shares (relative weight) is a number from 1-1024. 102 shares would equal 10% of the total cpu.
* -r, --ram
    - Memory limit (in megabytes)
* -s, --hostname_scheme
    - A base hostname scheme to use for the containers. Ex: dlweb would produce containers with hostnames of dlweb001, dlweb002, etc.
* -p, --port
    - Add ports to map to the container. host-port:container-port.  If the :is missing then host-port and container port are assumed to be identical
* -d, --delete_formation
    - Delete a formation of containers all at once.  
* -v, --volume
    - Create a bind mount. host-dir:container-dir:rw|ro. If "container-dir" is missing, then docker creates a new volume.
* -x, --verify
    - Verify that the cluster is in the correct state and move containers around that are on dead hosts.
* -z
    - Force the container to be brought up on a particular host server

Example Usage
-------------------------------
```
root@server01:autodock# python autodock.py create -u cholcomb -f clweb -n 1 -s clweb
2013-11-03 23:37:48,805 - urllib3.connectionpool - INFO - Starting new HTTP connection (1): server01
2013-11-03 23:37:58,961 - root - INFO - Checking if 9023 on server02 is open with salt-client
2013-11-03 23:37:59,130 - root - INFO - Adding app to formation clweb: clweb001 cpu_shares=100 ram=104857600 ports=22 host_server=server02
2013-11-03 23:37:59,130 - root - INFO - Starting up docker container on server02 with cmd: docker run -c=100 -d -h="clweb001" -m=104857600 -p 9023:22 server02:5000/sshd /usr/sbin/sshd -D
2013-11-03 23:37:59,353 - root - INFO - Bootstrapping clweb001 on server: server02 port: 9023
```
Salt State Files
-------------------------------

I have a state file setup for any hostname starting with cl* so clweb001, cldjango001, etc will all match my regex expression in the top.sls state file in Salt.
Try to keep your Salt installs as minimal as possible. The containers can really bloat in size easily.  

Testing the Code
-------------------------------

```
root@server01:autodock# python -m unittest -v etcd.TestEtcd
test_a_setkey (etcd.TestEtcd) ... ok
test_b_getkey (etcd.TestEtcd) ... ok
test_c_deletekey (etcd.TestEtcd) ... ok
test_d_directorylist (etcd.TestEtcd) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.193s

OK
ETCD JSON Objects
```
The docker cluster in etcd key is called: docker_cluster  
The JSON object that stores container configurations looks like this:  
A directory for the username /cholcomb  
A key for each formation: /cholcomb/owncloud and a value of:[ { "hostname": "owncloud01", "cpu-shares": 102, "ram": 100, "port": 8080, "host-server": "dldocker01", "mounts": [...]}, {...}]  
A formation consists of a list of apps  
