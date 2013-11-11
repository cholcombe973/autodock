class Systemd(object):
  '''
  Systemd will create/delete systemd files to make sure
  that the containers can survive a reboot

  The systemd files are configuration so they may need to live
  in the salt repo.  This is still to be determined.  Writing out a 
  yaml file to salt would fix this problem.  Write it to salt and 
  forget about it
  '''
  def __init__(self, manager, salt):
    self.manager = manager
    self.salt = manager.salt_client

