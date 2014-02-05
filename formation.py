import json
import unittest

from app import App

class Formation(object):
  '''
    A formation represents a group of application servers that are 
    working together to serve a common goal
    [ { "container_id": "61a6cb898d23",
        "username": "cholcomb",
        "hostname": "owncloud01", 
        "cpu-shares": 102, 
        "ram": 100, 
        "ports": [{"host_port":8080,"container_port":8080}], 
        "host-server": "dldocker01", 
        "mounts": [...]}, 
      {...}]
  '''

  def __init__(self, username, name, url_to_serve=None):
    self.application_list = []
    self.name = name
    self.username = username
    # The url that should be added to the load balancer for the apps to serve up
    self.url_to_serve = url_to_serve

  def add_app(self,
    container_id,
    hostname, 
    cpu_shares, 
    ram, 
    port_list,
    ssh_host_port, 
    ssh_container_port,
    host_server, 
    docker_image,
    volumes=None):
    '''
      NOTE - No support for volumes yet.  
      STRING          container_id #The container this app runs in
      STRING          hostname
      INTEGER         cpu_shares
      INTEGER         ram
      List of Ints    port_list
      INTEGER         host_port
      INTEGER         container_port
      STRING          host_server
      #LIST of        [host-dir]:[container-dir]:[rw|ro]
    '''
    app = App(container_id, self.username, hostname, cpu_shares, ram, 
      host_server, docker_image, ssh_host_port, volumes)

    #For each port in the port_list add it to the app
    for port in port_list:
      #Check to see if the host port is free first?
      #Throw an error if it is or just increment it?
      if ':' in port:
        port_list = port.split(':')
        app.add_port_mapping(port_list[0], port_list[1])
      else:
        app.add_port_mapping(port, port)

    #Add the default SSH port mapping
    app.add_port_mapping(ssh_host_port, ssh_container_port)

    self.application_list.append(app)

  def __str__(self):
    json_list = [x.get_json() for x in self.application_list]
    return json.dumps(json.dumps(json_list))

class TestFormation(unittest.TestCase):
  def test_addApp(self):
    self.assertEquals(1, 0)
