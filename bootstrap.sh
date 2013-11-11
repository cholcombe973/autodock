#!/bin/bash
apt-get update
apt-get -y install software-properties-common
mkdir -p /etc/salt/
touch /etc/salt/minion
cat <<EOF > /etc/salt/minion
master:
  - dlceph01
  - dlutility01

EOF

wget -O - http://bootstrap.saltstack.org | sh

#TIMEOUT=180
#COUNT=0
#while [ ! -f /etc/salt/pki/minion/minion_master.pub ]; do
#    echo "Waiting for salt install."
#    if [ "$COUNT" -ge "$TIMEOUT" ]; then
#        echo "minion_master.pub not detected by timeout"
#        exit 1
#    fi
#    sleep 5
#    COUNT=$((COUNT+5))
#done

echo "Calling highstate"
salt-call state.highstate &
