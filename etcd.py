import json
import logging
import pycurl
import re
import requests
import socket
import sys
import unittest

from StringIO import StringIO

class EtcdError(BaseException):
  #Generic etcd error
  pass

class Etcd(object):
  def __init__(self, logger, server=None):
    if server:
      self.server = server
    else:
      self.server = socket.gethostname()
    self.url = 'http://%(hostname)s:4001/v2/keys' % {
      'hostname': self.server}
    self.logger = logger

  def set_key(self, key, value):
    url = '%(base)s/%(key)s' % {
      'base': self.url,
      'key': key
    }
    data = 'value=%s' % value

    self.logger.debug("Saving data: %(data)s to %(url)s" %{
      'data': data,
      'url': url
    })
    storage = StringIO()

    curl = pycurl.Curl()
    curl.setopt(curl.URL, url)
    curl.setopt(curl.POSTFIELDS, data)
    curl.setopt(pycurl.FOLLOWLOCATION, 1)
    curl.setopt(pycurl.MAXREDIRS, 5)
    curl.setopt(curl.WRITEFUNCTION, storage.write)
    curl.setopt(pycurl.CUSTOMREQUEST, "PUT")
    curl.perform()
    response = curl.getinfo(pycurl.HTTP_CODE)
    curl.close()

    if response == requests.codes.ok:
      return True
    elif response == requests.codes.created:
      return True
    else:
      self.logger.error("ETCD returned %(status)s %(text)s" % {
        'status': response,
        'text': storage.getvalue()})
      return None

  def get_key(self, key):
    url = '%(base)s/%(key)s' % {
      'base': self.url,
      'key': key
    }
    self.logger.debug('Getting url: ' + url)
    response = requests.get(url)
    self.logger.debug('Response: ' + response.text)

    res = json.loads(response.text)
    if isinstance(res, list):
      raise ValueError('Key "%s" is a directory, expecting leaf (use \
list_directory() to get directory listing).' % key)      

    #Check to see if Etcd returned an error
    if 'errorCode' in res:
      raise EtcdError(res['errorCode'], res['message']) 

    try:
      return str(res['node']['value'])
    except KeyError:
      #Fallback on v1 functionality
      return str(res['value'])

  def delete_key(self, key):
    url = '%(base)s/%(key)s' % {
      'base': self.url,
      'key': key
    }

    response = requests.delete(url)
    if response.status_code == requests.codes.ok:
      return response.text
    else:
      response.raise_for_status()
      return None

  def list_directory(self, path):
    url = '%(base)s/%(path)s' % {
      'base': self.url,
      'path': path
    }
    response = requests.get(url)
    if response.status_code == requests.codes.ok:
      directory_list = []
      json_txt = json.loads(response.text)
      try:
        for entry in json_txt['node']['nodes']: 
          directory_list.append(str(entry['key']))
        return directory_list
      except KeyError:
        self.logger.error("Key ['node']['nodes'] not found in %(data)s" %{
          'data': json_txt
          })
    else:
      response.raise_for_status()
      return None

  def get_machines(self):
    url = '%(base)s/_etcd/machines' % {
      'base': self.url}
    res = json.loads(requests.get(url).text)

    #Check to see if Etcd returned an error
    if 'errorCode' in res:
      raise EtcdError(res['errorCode'], res['message']) 

    server_list = []
    for entry in res:
      server_list.append(str(entry['value']))

    return server_list

class TestEtcd(unittest.TestCase):
  def setUp(self):
    logger = logging.getLogger()
    stream = logging.StreamHandler(sys.stdout)
    stream.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream.setFormatter(formatter)
    logger.addHandler(stream)
    self.etcd = Etcd(logger)

  def test_a_setkey(self):
    ret = self.etcd.set_key('message', 'Hello World')
    self.assertTrue(ret)

  def test_b_getkey(self):
    self.etcd.set_key('message', 'Hello World')
    text = self.etcd.get_key('message')
    self.assertEqual(text, 'Hello World')

  def test_c_deletekey(self):
    #Set the key first before deleting it
    self.etcd.set_key('message', 'Hello World')

    text = self.etcd.delete_key('message')
    regex = re.compile(r'{"action":"delete","node":{"key":"/message",'
      '"modifiedIndex":\d+,"createdIndex":\d+},"prevNode":{"key":"/message"'
      ',"value":"Hello World","modifiedIndex":\d+,"createdIndex":\d+}}')
    self.assertRegexpMatches(text, regex)

  def test_d_directorylist(self):
    #List a directory in Etcd
    dir_list = self.etcd.list_directory('formations/cholcomb')
    self.assertIsInstance(dir_list, list)
