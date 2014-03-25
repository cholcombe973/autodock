class Apache(object):
  '''
    A python class to manage an apache proxypass load balancer
    Each app added to the load balancer will be given its own
    file.  
  '''
  def __init__(self, manager, logger, apache_server):
    self.manager = manager
    self.logger = logger
    self.apache_server = apache_server

  # Adds an app to the load balancer
  def add_vhost(self, app):
    pass

  # Adds an app to the load balancer
  def remove_vhost(self, app):
    pass
