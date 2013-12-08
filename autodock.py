import argparse
import logging
import sys

from manager import Manager
from verify import VerifyFormations

def main():
  logger = logging.getLogger()
  stream = logging.StreamHandler(sys.stdout)
  stream.setLevel(logging.INFO)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - '
    '%(message)s')
  stream.setFormatter(formatter)
  logger.addHandler(stream)

  parser = argparse.ArgumentParser(prog='autodock', 
    description='Autodock. The docker container automation tool.')
  subparsers = parser.add_subparsers(dest='mode', help='sub-command help')

  # create a parser for the "verify" command
  subparsers.add_parser('verify',
    help='Verify the formations in the cluster are working properly.')

  # create a parser and args for the "create" command
  create_parser = subparsers.add_parser('create', help='Create a new formation')
  create_parser.add_argument('-u', '--username', required=True, 
    help='The username for the formation')

  create_parser.add_argument('-f', '--formation', help='A Formation is a set of'
      ' infrastructure used to host Applications. Each formation includes Nodes'
      'that provide different services to the formation.', required=True)

  create_parser.add_argument('-n', '--number', type=int, 
    help='The number of containers to build, ex: 1. Default=1', default=1)

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

  create_parser.add_argument('-d', '--delete', type=bool, 
    help='Delete a formation of containers all at once.')

  create_parser.add_argument('-v', '--volume', action='append', 
    dest='volume_list', default=[], help='Create a bind mount. '
      'host-dir:container-dir:rw|ro. If "container-dir" is missing, '
      'then docker creates a new volume.')

  args = parser.parse_args()

  m = Manager(logger)
  if args.mode == 'verify':
    logger.info('Verifying the formation') 
    v = VerifyFormations(m, logger)
    v.start_verifying()
  else:
    logger.info('Creating a new formation')
    m.create_containers(args.username,
      args.number, args.formation, args.cpu_shares, args.ram,
      args.port_list, args.hostname_scheme, args.volume_list)
    return 0

if __name__ == "__main__":
  sys.exit(main())
