{# This is a Jinja2 template for a shell script to be run when
an instance starts. It sets up spotmark and AWS credentials
required for access to SQS. User code should be injected
by creating a child template inheriting from this. #}
#!/bin/bash

set -xe

# Make startup script output available in /var/log/user-data.log
# as well as to the  ec2-get-console-output command.
# See: http://alestic.com/2010/12/ec2-user-data-output
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

# python-dev is required for pyzmq to build
apt-get install -y git python-pip python-virtualenv python-dev

# Create boto config file (required for AWS access)
echo "[Credentials]
aws_access_key_id = {{ spotmark.aws_access_key }}
aws_secret_access_key = {{ spotmark.aws_secret_key }}" > ~/.boto

# Setup the Spotmark repo
git clone git://github.com/craigglennie/spotmark.git
virtualenv spotmark
cd spotmark
source bin/activate
pip install -r requirements.txt

{% block user_code %}{% endblock %}
