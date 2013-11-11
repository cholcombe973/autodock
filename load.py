class Load(object):
  '''
    An object representing the one, five and fifteen
    load on a host
  '''
  def __init__(self, hostname, one, five, fifteen):
    self.hostname = hostname
    self.one_min_load = float(one)
    self.five_min_load = float(five)
    self.fifteen_min_load = float(fifteen)

  def __str__(self):
    return  "host={host}, one={one}, five={five}, fifteen={fifteen}".format(
      host=self.hostname, one=self.one_min_load,
      five=self.five_min_load, fifteen=self.fifteen_min_load)
