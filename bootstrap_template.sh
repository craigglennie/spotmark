#!/bin/bash

set -xe

# Make output available in /var/log/user-data.log as well as to the
# ec2-get-console-output command.
# http://alestic.com/2010/12/ec2-user-data-output
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

# Required for s3cmd and boto
ACCESS_KEY_ID='%(access_key_id)s'
SECRET_ACCESS_KEY='%(secret_access_key)s'

# Controls whether metadata services try to use AWS web service
SPOTMARK_ENVIRONMENT='AWS'

# User-supplied envrionment variables
%(user_environment_variables)s
# User script
%(user_script)s

apt-get install -y git
apt-get install -y python-pip
pip install --upgrade boto

git clone git://github.com/craigglennie/spotmark.git
cd spotmark
# Clone the repo containing the test we're running as a submodule named 'test_code'
git submodule add -b %(git_repo_branch)s %(git_repo_uri)s test_code 

# Setup ZeroMQ
apt-get install -y python-dev
pip install pyzmq
