class App(object):
  '''
    An app or application has a hostname,
    cpu_shares, ram, port_list, volumes and a host_server
    it runs on.
  '''
  def __init__(self, container_id, username, hostname, 
    cpu_shares, ram, host_server, ssh_port, volume_list=None):

    self.container_id = container_id
    self.username = username
    self.hostname = hostname
    self.cpu_shares = int(cpu_shares)
    self.ram = int(ram)
    self.port_list = []
    self.host_server = host_server
    self.volume_list = volume_list
    self.ssh_port = int(ssh_port)

  def change_container_id(self, new_container_id):
    self.container_id = new_container_id

  def change_host_server(self, new_host_server):
    self.host_server = new_host_server
  
  def change_ram_limit(self, new_ram_limit):
    self.ram = int(new_ram_limit)

  def change_cpu_shares(self, new_cpu_shares):
    self.cpu_shares = int(new_cpu_shares)

  def add_port_mapping(self, host_port, container_port):
    port_map = "{host_port}:{container_port}".format(host_port=host_port,
      container_port=container_port)
    self.port_list.append(port_map)

  def get_json(self):
    return  {'container_id': self.container_id, 'username': self.username,
      'hostname': self.hostname, 'cpu_shares': self.cpu_shares,
      'ram': self.ram, 'port_list': self.port_list, 
      'host_server': self.host_server, 'volumes': self.volume_list,
      'ssh_port': self.ssh_port}
