#!/bin/bash
apt-get update
apt-get -y install software-properties-common
echo "Acquire::http::Proxy \"http://192.168.1.21:3142\";" > /etc/apt/apt.conf.d/02proxy
mkdir -p /etc/salt/
touch /etc/salt/minion
cat <<EOF > /etc/salt/minion
master:
  - dlceph01
  - dlceph02
  - dlceph03

EOF

wget -O - http://bootstrap.saltstack.org | sh

echo "Calling highstate"
salt-call state.highstate &
