{# This is a Jinja2 template for a shell script to be run when
an instance starts #}
#!/bin/bash

set -xe

# Make output available in /var/log/user-data.log as well as to the
# ec2-get-console-output command.
# http://alestic.com/2010/12/ec2-user-data-output
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

# Required for s3cmd and boto
ACCESS_KEY_ID='{{ aws.access_key_id }}'
SECRET_ACCESS_KEY='{{ aws.secret_access_key }}'

apt-get install -y git python-pip virtualenv
pip install --upgrade boto

# Setup the Spotmark repo
git clone git://github.com/craigglennie/spotmark.git
virtualenv spotmark
cd spotmark
source bin/activate
pip install -r requirements.txt

# Setup ZeroMQ
apt-get install -y python-dev
pip install pyzmq

{% block user_code %}{% endblock %}
