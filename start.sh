#!/bin/bash
# This should be called on the container start to make sure everything
# is up and working properly
if [ -z "$(pgrep -f /usr/sbin/sshd)" ]
  then
    # start up sshd
    echo "Starting sshd" >> startup.log
    /usr/sbin/sshd -D&
fi

if [ -z "$(pgrep -f /usr/sbin/cron)" ]
  then
    # start up cron
    echo "Starting cron" >> startup.log
    /usr/sbin/cron&
fi

if hash salt 2>/dev/null; then
  echo "Calling salt" >> startup.log
  salt-call state.highstate&
else
  echo "Salt is not installed.  Bootstrapping"
  /root/bootstrap.sh
fi
