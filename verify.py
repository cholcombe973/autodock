'''
  This class performs a few functions:
  1. If the host is up and the container is down it starts the container
  2. Verifies a container is running
  3. Verifies a container has cron running.  Calls start.sh if needed.

'''
import json
import paramiko
import salt.client
import time

from circularlist import CircularList
from etcd import Etcd
from formation import Formation
from paramiko import SSHException
from pyparsing import alphas, Literal, srange, Word

class VerifyFormations(object):
  def __init__(self, manager, logger):
    self.logger = logger
    self.salt_client = salt.client.LocalClient()
    self.manager = manager
    self.etcd = Etcd(logger)

  def start_verifying(self):
    # Parse out the username and formation name 
    # from the ETCD directory string
    formation_parser = Literal('/formations/') + \
      Word(alphas).setResultsName('username') + Literal('/') + \
      Word(srange("[0-9a-zA-Z_-]")).setResultsName('formation_name')

    # call out to ETCD and load all the formations
    formation_list = []

    user_list = self.etcd.list_directory('formations')
    if user_list:
      for user in user_list:
        formations = self.etcd.list_directory(user)
        for formation in formations:
          parse_results = formation_parser.parseString(formation)
          if parse_results:
            formation_name = parse_results['formation_name']
            username = parse_results['username']

            self.logger.info('Attempting to load formation: {formation_name} '
              'with username: {username}'.format(formation_name=formation_name,
                username=username))
            f = self.load_formation_from_etcd(username, formation_name)
            formation_list.append(f)
          else:
            self.logger.error("Could not parse the ETCD string")

      if formation_list:
        # TODO Use background salt jobs
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
            self.logger.info("Running verification on app: "
              "{app_name}".format(app_name=app.hostname))
            results = self.salt_client.cmd(app.host_server, 'cmd.run', 
              ['docker ps | grep {container_id}'.format(container_id=app.container_id)], 
              expr_form='list')
            if results:
              self.logger.debug("Salt return: {docker_results}".format(
                docker_results=results[app.host_server]))
              if results[app.host_server] == "":
                self.logger.error("App {app} is not running!".format(
                  app=app.hostname))
                # Start the app back up and run start.sh on there
                self.start_application(app)
              else:
                self.logger.info("App {app} is running.  Checking if "
                  "cron is running also".format(app=app.hostname))
                # Check if cron is running on the container and bring it back 
                # up if needed
                # Log in with ssh and check if cron is up and running
                self.check_running_application(app)
            else:
              self.logger.error("Call out to server {server} failed. Moving it".format(
                server=app.host_server))
              # move the container
              self.move_application(app)

  # Start an application that isn't running
  def start_application(self, app):
    # Start the application and run start.sh to kick off cron
    self.logger.info("Starting app {app} with docker id: {app_id} up".format(
      app=app.hostname, app_id=app.container_id))
    results = self.salt_client.cmd(app.host_server, 'cmd.run', 
      ['docker start {container_id}'.format(container_id=app.container_id)], 
      expr_form='list')
    self.logger.debug(results)
    if results:
      if "Error: No such container" in results[app.host_server]:
        # We need to recreate the container
        self.logger.error("Container is missing on the host!. "
          "Trying to recreate")
        self.manager.start_application(app)
        self.logger.info("Sleeping 2 seconds while the container starts")
        time.sleep(2)
        self.manager.bootstrap_application(app)
      elif "Error: start: No such container:" in results[app.host_server]:
        # Seems the container already exists but won't start.  Bug?
        self.logger.error("Container failed to start")
        self.move_application(app)
      else:
        self.check_running_application(app)
    else:
      # Move the container to another host, this host is messed up
      self.logger.error("Failed to start {container_id} on host {host}".format(
        container_id=app.container_id, host=app.host_server))
      self.move_application(app)

  # Move an application to another host and record the change in etcd
  def move_application(self, app):
    old_host = app.host_server
    cluster_list = self.manager.get_docker_cluster()
    circular_cluster_list = CircularList(
      self.manager.order_cluster_by_load(cluster_list))

    if app.host_server in circular_cluster_list:
      index = circular_cluster_list.index(app.host_server)
      app.host_server = circular_cluster_list[index+1].hostname
    else:
      # Assign the first one in the list if not found above
      app.host_server = circular_cluster_list[0].hostname

    self.logger.info("Moving app {app_name} from {old_host} to {new_host}".format(
      app_name=app.hostname, old_host=old_host, new_host=app.host_server))

    self.logger.info("Bootstrapping the application on the new host")
    self.start_application(app)

  # Log into the application via ssh and check everything
  def check_running_application(self, app):
    # TODO
    # Use the docker top command to see if cron is running instead of using ssh
    try:
      ssh = paramiko.SSHClient()
      ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      # Move this user/pass into a config file
      ssh.connect(hostname=app.host_server, port=app.ssh_port, 
        username='root', password='newroot')
      # Is cron running?
      # If not run start.sh
      stdin, stdout, stderr = ssh.exec_command("pgrep cron")
      output = stdout.readlines()
      self.logger.debug(output)

      if len(output) == 0:
        # cron isn't running
        self.logger.info("Cron is not running.  Starting it back up")
        stdin, stdout, stderr = ssh.exec_command("/root/start.sh")
      else:
        self.logger.info("Cron is running. Exiting")
      ssh.close()
    except SSHException:
      self.logger.error("Failed to log into server.  Shutting it down and "\
        "cleaning up the mess.")
      self.delete_container(app.host_server, app.container_id)

  # Load the formation and return a Formation object
  def load_formation_from_etcd(self, username, formation_name):
    f = Formation(username,formation_name) 
    app_list = json.loads(json.loads(
      self.etcd.get_key('/formations/{username}/{formation_name}'.format(
        username=username, formation_name=formation_name))))
    for app in app_list:
      # If our host doesn't support swapping we're going to get some garbage 
      # message in here
      if "WARNING" in app['container_id']:
        app['container_id'] = app['container_id'].replace("WARNING: Your "\
          "kernel does not support memory swap capabilities. Limitation discarded.\n","")

      # Set volumes if needed
      volumes = None
      if app['volumes']:
        self.logger.info("Setting volumes to: " + ''.join(app['volumes']))
        volumes = app['volumes']

      f.add_app(app['container_id'], app['hostname'], app['cpu_shares'],
        app['ram'], app['port_list'], app['ssh_port'], 22, app['host_server'], volumes)

    # Return fully parsed and populated formation object
    return f
