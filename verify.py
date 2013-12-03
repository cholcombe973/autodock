'''
  This class performs a few functions:
  1. If the host is up and the container is down it starts the container
  2. Verifies a container is running
  3. Verifies a container has cron running.  Calls start.sh if needed.

'''
import json
import salt.client

from etcd import Etcd
from formation import Formation
from pyparsing import alphas, Literal, srange, Word

class VerifyFormations(object):
  def __init__(self, logger):
    self.logger = logger
    self.salt_client = salt.client.LocalClient()
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

            self.logger.info('Attempting to load formation: ' + formation_name + ' username: ' + username)
            f = self.load_formation_from_etcd(username, formation_name)
            formation_list.append(f)
          else:
            self.logger.error("Could not parse the ETCD string")

      if formation_list:
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
            self.logger.info("Running verifcation on app: "
              "{app_name}".format(app_name=app.hostname))
            results = self.salt_client.cmd(app.host_server, 'cmd.run', 
              ['docker ps | grep {container_id}'.format(container_id=app.container_id)], 
              expr_form='list')
            if results:
              self.logger.debug("Salt return: {docker_results}".format(docker_results=results[app.host_server]))
              if results[app.host_server] == "":
                self.logger.error("App {app} is not running!".format(app=app.hostname))
                # TODO write me, start the app back up and run start.sh on there to start the cron job
              else:
                self.logger.info("App {app} is running.  Checking if cron is running also".format(app=app.hostname))
                # TODO write me, check if cron is running on the container and bring it back up if needed
                # Log in with ssh and check if cron is up and running
                # app.host_server
                # app.hostname
                # app.ssh_port
            else:
              self.logger.error("Call out to server {server} failed".format(server=app.host_server))
              # TODO write me, move the container

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

      f.add_app(app['container_id'], app['hostname'], app['cpu_shares'],
        app['ram'], app['port_list'], app['ssh_port'], 22, app['host_server'])

    # Return fully parsed and populated formation object
    return f
