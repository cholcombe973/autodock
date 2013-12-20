# Simple SSH container
#
# VERSION    0.1

FROM ubuntu
# make sure the package repository is up to date
RUN echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list
RUN apt-get update

# Install openssh, mercurial and a few other utilityes
RUN apt-get install -y openssh-server python-bcrypt mercurial mercurial-common python-dev python-pip vim

# Run the start script which bootstraps the container
ADD start.sh /root/start.sh

CMD    ["/root/start.sh"]
