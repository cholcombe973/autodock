class Nginx(object):
  '''
    A python class to manage the nginx cluster

  An example nginx load balancing config:
  http {
    upstream web_rack {
      server 10.0.0.1:80;
      server 10.0.0.2:80;
      server 10.0.0.3:80;
    }
 
    server {
      listen 80;
      server_name www.example.com;
      location / {
          proxy_pass http://web_rack;
      }
    }
  }
  '''
  def __init__(self, manager, logger):
    self.manager = manager
    self.salt = manager.salt_client
    self.logger = logger

  #TODO 
  def add_vhost(self, cluster_config):
    #If the site file exists, blow it away and recreate it
    #We need a server list, ports and a listen name
    nginx_cluster = self.manager.get_load_balancer_cluster()

  #TODO
  def remove_vhost(self, cluster_config):
    pass

  def reload_nginx(self, host):
    #Tells nginx to reload its config
    self.salt.cmd(host, 'cmd.run', ['service nginx reload'], expr_form='list')

