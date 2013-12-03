import unittest

class CircularList(list):
    '''
    A list that wraps around instead of throwing an index error.
    
    Works like a regular list:
    >>> cl = CircularList([1,2,3])
    >>> cl
    [1, 2, 3]
    
    >>> cl[0]
    1
    
    >>> cl[-1]
    3
    
    >>> cl[2]
    3
    
    Except wraps around:
    >>> cl[3]
    1
    
    >>> cl[-4]
    3
    
    Slices work
    >>> cl[0:2]
    [1, 2]
    
    but only in range.
    '''
    def __getitem__(self, key):
      # try normal list behavior
      try:
        return super(CircularList, self).__getitem__(key)
      except IndexError:
        pass
      # key can be either integer or slice object,
      # only implementing int now.
      try:
        index = int(key)
        index = index % self.__len__()
        return super(CircularList, self).__getitem__(index)
      except ValueError:
        raise TypeError

class TestCircularList(unittest.TestCase):
  def test_cicular_list_wrap_forward(self):
    cl = CircularList([1,2,3])
    #make sure it wraps properly
    self.assertEqual(cl[3], 1)

  def test_cicular_list_wrap_backward(self):
    cl = CircularList([1,2,3])
    #make sure it wraps properly
    self.assertEqual(cl[-1], 3)
