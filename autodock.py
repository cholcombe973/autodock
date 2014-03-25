import argparse
import ConfigParser
import logging
import os.path
import sys

from appbackup import AppBackup
from edit import FormationEditor
from manager import Manager
from verify import VerifyFormations

def parse_config(cfg_file):
  # If a config file is present use it to populate various default
  # values
  config_options = {}
  config = ConfigParser.ConfigParser()
  if os.path.exists(cfg_file):
    config.read(cfg_file)
    # playing it safe with the parsing.  Missing sections will be ignored

    try:
      backup_options = config.items('backup')
      config_options['backup'] = backup_options
    except ConfigParser.NoSectionError:
      config_options['backup'] = None

    try:
      manager_options = config.items('manager')
      config_options['manager'] = manager_options
    except ConfigParser.NoSectionError:
      config_options['manager'] = None

    try:
      verify_options = config.items('verify')
      config_options['verify'] = verify_options
    except ConfigParser.NoSectionError:
      config_options['verify'] = None

    try:
      etcd_options = config.items('etcd')
      config_options['etcd'] = etcd_options
    except ConfigParser.NoSectionError:
      config_options['etcd'] = None

    return config_options

def parse_cli_args():
  parser = argparse.ArgumentParser(prog='autodock', 
    description='Autodock. The docker container automation tool.')
  subparsers = parser.add_subparsers(dest='mode', help='sub-command help')

  # create a parser for the "list" command
  list_parser = subparsers.add_parser('list',
    help='List the formations a user owns.')
  list_parser.add_argument('-u', '--username', required=True, 
    help='The username to list formations for')

  # create a parser for the "edit" command
  edit_parser = subparsers.add_parser('edit',
    help='Edit a formation a user owns.')
  edit_parser.add_argument('-u', '--username', required=True,
    help='The username who owns the formation')

  # create a parser for the "verify" command
  subparsers.add_parser('verify',
    help='Verify the formations in the cluster are working properly.')

  # create a parser for the "backup" command
  backup_parser = subparsers.add_parser('backup',
    help='Backup the formation specified by username and formation name.')
  backup_parser.add_argument('-u', '--username', required=True, 
    help='The username who owns the formation')
  backup_parser.add_argument('-f', '--formation', help='A Formation is a set of'
      ' infrastructure used to host Applications. Each formation includes Nodes'
      'that provide different services to the formation.', required=True)
  backup_parser.add_argument('-d', '--directory', required=True, 
    help='The directory to back up docker containers into')

  # create a parser for the "delete" command
  delete_parser = subparsers.add_parser('delete',
    help='Delete the formation specified by username and formation name.')
  delete_parser.add_argument('-u', '--username', required=True, 
    help='The username who owns the formation')
  delete_parser.add_argument('-f', '--formation', help='A Formation is a set of'
      ' infrastructure used to host Applications. Each formation includes Nodes'
      'that provide different services to the formation.', required=True)

  # create a parser and args for the "create" command
  create_parser = subparsers.add_parser('create', help='Create a new formation')
  create_parser.add_argument('-u', '--username', required=True, 
    help='The username for the formation')

  create_parser.add_argument('-f', '--formation', help='A Formation is a set of'
      ' infrastructure used to host Applications. Each formation includes Nodes'
      'that provide different services to the formation.', required=True)

  create_parser.add_argument('-n', '--number', type=int, 
    help='The number of containers to build, ex: 1. Default=1', default=1)

  create_parser.add_argument('-i', '--image', default='s2disk/baseimage:0.9.8',
    help='The docker image to use, ex: ubuntu-base. Note: This image to use '
    'needs to be identical across your cluster.')

  create_parser.add_argument('-c', '--cpu_shares', type=int, 
    help='A percentage of the cpu that the container is allowed '
      'to use. CPU shares (relative weight) is a number from 1-1024.', 
      default=100)

  create_parser.add_argument('-r', '--ram', type=int, 
    help='Memory limit in megabytes. Default=100MB', default=100)

  create_parser.add_argument('-s', '--hostname_scheme', 
    help='A base hostname scheme to use for the containers. Ex: dlweb '
    'would produce containers with hostnames of dlweb001, dlweb002, etc.', 
    required=True)

  create_parser.add_argument('-p', '--port', action='append', dest='port_list',
    help='Add ports to map to the container. host-port:container-port.  If the'
      ': is missing then host-port and container port are assumed to be '
      'identical', default=[])

  create_parser.add_argument('-z', '--host_server', dest='host_server',
    help='Force the application to be put on a particular host server',
    default=None)

  create_parser.add_argument('-v', '--volume', action='append', 
    dest='volume_list', default=[], help='Create a bind mount. '
      'host-dir:container-dir:rw|ro. If "container-dir" is missing, '
      'then docker creates a new volume.')

  return parser.parse_args()

def main():
  logger = logging.getLogger()
  stream = logging.StreamHandler(sys.stdout)
  stream.setLevel(logging.INFO)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - '
    '%(message)s')
  stream.setFormatter(formatter)
  logger.addHandler(stream)

  args = parse_cli_args()

  #if os.path.exists('autodock.config'):
  #  config_dict = parse_config('autodock.config')
    
  m = Manager(logger)
  if args.mode == 'list':
    logger.info('Listing the formations')
    m.list_formations(args.username)
    return 0
  elif args.mode == 'edit':
    logger.info('Editing the formation')
    e = FormationEditor(m, logger)
    e.edit_formation('args')
    return 0
  elif args.mode == 'verify':
    logger.info('Verifying the formation') 
    v = VerifyFormations(m, logger)
    v.start_verifying()
    return 0
  elif args.mode == 'backup':
    logger.info('Backing up a formation')
    b = AppBackup(m, logger)
    b.backup_formation(args.username, args.formation, args.directory)
    return 0
  elif args.mode == 'delete':
    logger.info('Deleting a formation')
    m.delete_formation(args.username, args.formation)
  else:
    logger.info('Creating a new formation')
    m.create_containers(args.username,
      args.number, args.formation, args.cpu_shares, args.ram,
      args.port_list, args.hostname_scheme, args.volume_list, 
      args.image, args.host_server)
    return 0

if __name__ == "__main__":
  sys.exit(main())
