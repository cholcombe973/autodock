#!/bin/bash
apt-get update
apt-get -y install software-properties-common
#A helper which caches apt packages.  Delete if not using
echo "Acquire::http::Proxy \"http://192.168.1.21:3142\";" > /etc/apt/apt.conf.d/02proxy
mkdir -p /etc/salt/
touch /etc/salt/minion
cat <<EOF > /etc/salt/minion
# ** NOTE CHANGE THESE TO YOUR salt multi master cluster **
master:
  - dlceph01
  - dlceph02
  - dlceph03

EOF

wget -O - http://bootstrap.saltstack.org | sh

echo "Calling highstate"
salt-call state.highstate &
