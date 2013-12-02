import json
import logging
import paramiko
from paramiko import SSHException
from pyparsing import Combine, Literal, OneOrMore, nums, Word
import salt.client
import sys
import time
import unittest

from circularlist import CircularList
from etcd import Etcd
from formation import Formation
from load import Load

class ManagerError(BaseException):
  # Generic manager error
  pass

class Manager(object):
  '''
    A manager to orchestrate the creation and 
    deletion of container clusters
  '''
  def __init__(self, logger):
    self.salt_client = salt.client.LocalClient()
    self.etcd = Etcd(logger)
    self.logger = logger

  def fqdn_to_shortname(self, fqdn):
    if '.' in fqdn:
      return fqdn.split('.')[0]
    else:
      return fqdn

  def check_port_used(self, host, port):
    self.logger.info("Checking if {port} on {host} is open with salt-client".format(
      host=host, port=port))
    results = self.salt_client.cmd(host, 'cmd.run', 
      ['netstat -an | grep %s | grep tcp | grep -i listen' % port], 
      expr_form='list')
    self.logger.debug("Salt return: {lsof}".format(lsof=results[host]))

    if results[host] is not '':
      return True
    else:
      return False

  # TODO
  def verify_formations(self):
    # Parse out the username and formation name 
    # from the ETCD directory string
    formation_parser = Literal('/formations/') + \
      Word(alphas).setResultsName('username') + Literal('/') + \
      Word(alphanums).setResultsName('formation_name')

    # call out to ETCD and load all the formations
    formation_list = []

    user_list = self.etcd.list_directory('formations')
    if user_list:
      for user in user_list:
        username = user_parser.parseString(user)['username']
        formation_list = self.etcd.list_directory(user)
        for formation in formation_list:
          users_formation = self.etcd.get_key(formation)
          parse_results = formation_parse.parseString(formation)
          if parse_results:
            formation_name = parseResults['formation_name']
            username = parseResults['username']
            f = self.load_formation_from_etcd(username, formation_name)
            formation_list.append(f)
          else:
            self.logger.error("Could not parse the ETCD string")
            raise ManagerError("Could not parse the ETCD string returned "
              "{ret_string}".format(ret_string=formation))

      if formation_list:
        # This is where things get tricky
        # Start verifying things
        # Ask salt to do these things for me and give me back an job_id
        # results = self.salt_client.cmd_async(host, 'cmd.run', 
        #   ['netstat -an | grep %s | grep tcp | grep -i listen' % port], 
        #   expr_form='list')
        # 
        # salt-run jobs.lookup_jid <job id number>
        for f in formation_list:
          for app in f.application_list:
            # Check to make sure it's up and running
            self.logger.info("Running verifcation on formation: "
              "{formation_name}".format(formation_name=f.name))
            pass

  # TODO
  def check_for_existing_formation(self, formation_name):
    # If the user passed in an existing formation name lets append to it
    pass

  def get_docker_cluster(self):
    # Return a list of docker hosts
    cluster = self.etcd.get_key('docker_cluster')
    if cluster is not None:
      return cluster.split(',')
    else:
      return None

  def get_load_balancer_cluster(self):
    # Return a list of nginx hosts
    cluster = self.etcd.get_key('nginx_cluster')
    if cluster is not None:
      return cluster.split(',')
    else:
      return None

  def order_cluster_by_load(self, cluster_list):
    # Sample salt output
    # {'dlceph01.drwg.local': '0.27 0.16 0.15 1/1200 26234'}

    # define grammar
    point = Literal('.')
    number = Word(nums) 
    floatnumber = Combine( number + point + number)
    float_list = OneOrMore(floatnumber)

    results = self.salt_client.cmd(','.join(cluster_list), 'cmd.run', ['cat /proc/loadavg'], expr_form='list')
    load_list = []
    self.logger.debug("Salt load return: {load}".format(load=results))

    for host in results:
      host_load = results[host]
      match = float_list.parseString(host_load)
      if match:
        one_min = match[0]
        five_min = match[1]
        fifteen_min = match[2]
        self.logger.debug("Adding Load({host}, {one_min}, {five_min}, {fifteen_min}".format(
          host=host, one_min=one_min, five_min=five_min, fifteen_min=fifteen_min))
        load_list.append(Load(host, one_min, five_min, fifteen_min))
      else:
        self.logger.error("Could not parse host load output")

    # Sort the list by fifteen min load
    load_list = sorted(load_list, key=lambda x: x.fifteen_min_load)
    for load in load_list:
      self.logger.debug("Sorted load list: " + str(load))

    return load_list

  # Load the formation and return a Formation object
  def load_formation_from_etcd(self, username, formation_name):
    f = Formation(username,formation_name) 
    app_list = json.loads(json.loads(
      self.etcd.get_key('/formations/{username}/{formation_name}'.format(
        username=username, formation_name=formation_name))))
    for app in app_list:
      f.add_app(app['container_id'], app['hostname'], app['cpu_shares'],
        app['ram'], app['port_list]', app['ssh_port'], 22, app['host_server'])

    # Return fully parsed and populated formation object
    return f

  def save_formation_to_etcd(self, formation):
    name = formation.name
    username = formation.username

    self.etcd.set_key('formations/{username}/{formation_name}'.format(
      username=username, formation_name=name), formation)

  # TODO write code to add new container(s) to load balancer
  def add_app_to_nginx(self, app):
    pass

  def start_formation(self, formation):
    # Run a salt cmd to startup the formation
    docker_command = "docker run -c={cpu_shares} -d -h=\"{hostname}\" -m={ram} "\
      "-name=\"{hostname}\" {port_list} {volume_list} {image} /usr/sbin/sshd -D"

    for app in formation.application_list:
      port_list = ' '.join(map(lambda x: '-p ' + x, app.port_list))
      volume_list = ' '.join(map(lambda x: '-v ' + x, app.volume_list))

      d = docker_command.format(cpu_shares=app.cpu_shares, 
        hostname=app.hostname, ram=app.ram, image='dlcephgw01:5000/sshd', 
        port_list=port_list, volume_list=volume_list) 

      self.logger.info("Starting up docker container on {host_server} with cmd: {docker_cmd}".format(
        host_server=app.host_server, docker_cmd=d))

      salt_process = self.salt_client.cmd(app.host_server,'cmd.run', [d], expr_form='list')
      container_id = salt_process[app.host_server]
      if container_id:
        app.change_container_id(container_id)

  def bootstrap_formation(self, f):
    for app in f.application_list:
      # Log into the host with paramiko and run the salt bootstrap script 
      host_server = self.fqdn_to_shortname(app.host_server)

      self.logger.info("Bootstrapping {hostname} on server: {host_server} port: {port}".format(
        hostname=app.hostname, 
        host_server=host_server,
        port=app.ssh_port))

      try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=host_server, port=app.ssh_port, 
          username='root', password='newroot')

        transport = paramiko.Transport((host_server, app.ssh_port))
        transport.connect(username = 'root', password = 'newroot')
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put('bootstrap.sh', '/root/bootstrap.sh')
        sftp.put('start.sh', '/root/start.sh')

        ssh.exec_command("chmod +x /root/bootstrap.sh")
        ssh.exec_command("chmod +x /root/start.sh")
        stdin, stdout, stderr = ssh.exec_command("bash /root/start.sh")
        self.logger.debug(''.join(stdout.readlines()))
        ssh.close()
      except SSHException:
        self.logger.error("Failed to log into server.  Shutting it down and cleaning up the mess.")
        self.delete_container(app.host_server, app.container_id)

  # Stops and deletes a container
  def delete_container(self, host_server, container_id):
    results = self.salt_client.cmd(host_server, 'cmd.run', 
      ['docker stop {container_id}'.format(container_id=container_id)], 
      expr_form='list')
    self.logger.debug("Salt return: {stop_cmd}".format(stop_cmd=results[host_server]))

    results = self.salt_client.cmd(host_server, 'cmd.run', 
      ['docker rm {container_id}'.format(container_id=container_id)], 
      expr_form='list')
    self.logger.debug("Salt return: {rm_cmd}".format(rm_cmd=results[host_server]))

  def create_containers(self, user, number, formation_name,
    cpu_shares, ram, port_list, hostname_scheme, volume_list):

    f = Formation(user, formation_name)
    # Convert ram to bytes from MB
    ram = ram * 1024 * 1024

    # Get the cluster machines on each creation
    cluster_list = self.get_docker_cluster()
    circular_cluster_list = CircularList(self.order_cluster_by_load(cluster_list))

    # Loop for the requested amount of containers to be created
    for i in range(1, number+1):
      # [{"host_port":ssh_host_port, "container_port":ssh_container_port}]
      ssh_host_port = 9022 + i
      ssh_container_port = 22
      host_server = circular_cluster_list[i].hostname
      validated_ports = []

      while self.check_port_used(host_server, ssh_host_port):
        ssh_host_port = ssh_host_port +1

      for port in port_list:
        self.logger.info("Checking if port {port} on {host} is in use".format(
          port=port, host=host_server))
        if ':' in port:
          ports = port.split(':')

          # Only check if the host port is free.  The container port should be free
          while self.check_port_used(host_server, ports[0]):
            ports[0] = int(ports[0]) + 1

          # Add this to the validated port list
          validated_ports.append('{host_port}:{container_port}'.format(
            host_port = str(ports[0]),
            container_port = str(ports[1])))
        else:
          while self.check_port_used(host_server, port):
            port = int(port) + 1
          validated_ports.append(str(port))

      self.logger.info('Adding app to formation {formation_name}: {hostname}{number} cpu_shares={cpu} '
        'ram={ram} ports={ports} host_server={host_server}'.format(formation_name=formation_name,
          hostname=hostname_scheme, number=str(i).zfill(3), cpu=cpu_shares, ram=ram, 
          ports=validated_ports, host_server=host_server))

      f.add_app(None, '{hostname}{number}'.format(hostname=hostname_scheme, 
        number=str(i).zfill(3)), cpu_shares, ram, validated_ports, ssh_host_port, 
        ssh_container_port, circular_cluster_list[i].hostname, volume_list)

    # Lets get this party started
    self.start_formation(f)
    self.logger.info("Sleeping 2 seconds while the container starts")
    time.sleep(2)
    self.bootstrap_formation(f)

    self.logger.info("Saving the formation to ETCD")
    self.save_formation_to_etcd(f)

class TestManager(unittest.TestCase):
  def test_checkPortUsed(self):
    self.assertEquals(1, 0)

  def test_getDockerCluster(self):
    self.assertEquals(1, 0)

  def test_getLoadBalancerCluster(self):
    self.assertEquals(1, 0)

  def test_orderClusterByLoad(self):
    self.assertEquals(1, 0)

  def test_deleteContainer(self):
    self.assertEquals(1, 0)

  def test_saveFormationToEtcd(self):
    logger = logging.getLogger()
    stream = logging.StreamHandler(sys.stdout)
    stream.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    manager = Manager(logger)
    expected_text = '[{"username": "cholcomb", "cpu-shares": 102, '\
      '"ram": 100, "hostname": "app01", "ports": [{"host_port": 8080, '\
      '"container_port": 8080}], "host_server": "dlceph02"}]'
    username = 'cholcomb'
    formation_name = 'test_formation'
    f = Formation(username, formation_name)
    f.add_app(username, 'app01', 102, 100, [{"host_port":8080, "container_port":8080}], 'dlceph02')
    manager.save_formation_to_etcd(f)
    etcd_ret = manager.etcd.get_key('{username}/{hostname}'.format(username=username, hostname=formation_name))

    logger.debug("Etcd_ret: %s" % etcd_ret)
    logger.debug("Expected text: %s" % expected_text)
    self.assertEquals(etcd_ret, expected_text)
