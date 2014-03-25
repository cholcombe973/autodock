'''
  Automates the backing up of customer containers
'''
import salt.client

from datetime import datetime
from etcd import Etcd
import os
import os.path

class AppBackup(object):
  def __init__(self, manager, logger):
    self.etcd = Etcd(logger)
    self.logger = logger
    self.manager = manager
    self.salt_client = salt.client.LocalClient()

  # Backup this users formation to /mnt/ceph/docker_customer_backups
  def backup_formation(self, user, formation, backup_directory):
    self.logger.info('Saving the formation {formation}'.format(
      formation=formation))
    formation = self.manager.load_formation_from_etcd(user, formation)
    for app in formation.application_list:
      self.logger.info('Running commit on {hostname}'.format(
        hostname=app.hostname))
      # Try to commmit the container and wait 10 mins for this to return
      results = self.salt_client.cmd(app.host_server, 'cmd.run', 
        ['docker commit {container_id}'.format(container_id=app.container_id)],
        expr_form='list', timeout=1200)
      if results:
        self.logger.debug("Salt return: {commit}".format(
          commit=results[app.host_server]))

        if "Error: No such container" in results[app.host_server]:
          self.logger.error('Could not find container')
        else:
          if not os.path.exists(backup_directory):
            #Looks like the backup directory doesn't exist.  Lets create it
            self.logger.info('Creating the missing backup directory')
            os.makedirs(backup_directory)

          current_date = datetime.now()
          commit_id = results[app.host_server]
          self.logger.info('Running save on {hostname}'.format(
            hostname=app.hostname))
          results = self.salt_client.cmd(app.host_server, 'cmd.run', 
            ['docker save {image_id} > {backup_directory}/{hostname}.{year}-{month}-{day}.tar'.format(
                image_id=commit_id[0:12], 
                year=current_date.year,
                month=current_date.month,
                day=current_date.day,
                backup_directory=backup_directory,
                hostname=app.hostname)], 
            expr_form='list', timeout=1200)
          if results:
            self.logger.debug("Salt return: {save}".format(
              save=results[app.host_server]))
          self.logger.info('Cleaning up the commit image')
          self.salt_client.cmd(app.host_server, 'cmd.run',
            ['docker rmi {image_id}'.format(image_id=commit_id[0:12])], 
            expr_form='list')
          self.logger.info('Done saving app')
