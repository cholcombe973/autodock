'''
  This class will edit a formation currently
  stored in etcd. 
'''
from etcd import Etcd
class FormationEditor(object):
  def __init__(self, manager, logger):
    self.logger = logger
    self.manager = manager
    self.etcd = Etcd(logger)

