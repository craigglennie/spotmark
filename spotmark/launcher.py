from datetime import datetime, timedelta
import boto

# Ubuntu 13.04 64-bit instance-store
DEFAULT_AMI = 'ami-5dd0ba34'
BOOTSTRAP_TEMPLATE = "startup_template.sh"

def get_most_recent_spot_price(instance_type, environment="Linux/UNIX"):
    start_time = datetime.utcnow() - timedelta(seconds=3600)
    prices = boto.connect_ec2().get_spot_price_history(
        start_time=start_time.isoformat(),
        instance_type=instance_type,
        product_description=environment
    )
    return prices[0].price

def get_user_data(access_key_id, secret_access_key, git_repo_uri, get_repo_branch, environment_variables=None, user_script=None):
    """Returns the user data shell script used to bootstrap an instance.
    access_key_id, security_group, sqs_queue_name: Exported as environment variables for boto
    git_repo_uri: URI to a Git repo containing code to be downloaded and run by the machine.
    """

    user_script = user_script or ''

    environment_variables = environment_variables or {}
    user_environment_variables = "\n".join(
        "%s='%s'" % (key, value) for key, value in environment_variables.items()
    )

    user_data = open(BOOTSTRAP_TEMPLATE).read() % locals()
    return user_data


class ScriptedInstanceLauncher(object):
    """Launches an EC2 instance to run a user-supplied script""" 

    instance_ids = []
    _ec2 = None    

    @property
    def ec2(self):
        if not self._ec2:
            self._ec2 = boto.connect_ec2(region=self.region)
        return self._ec2

    @property
    def instance_count(self):
        return len(self.instance_ids)

    def get_public_ip(self, instance_id):
        [reservation] = self.ec2.get_all_instances(instance_id)
        [ip] = [i.ip_address for i in reservation.instances if i.id == instance_id]
        return ip

    def __init__(self, instance_type, security_group, key_name, ami=None, user_data=None, region_name='us-east-1', availability_zone=None):
        self.instance_type = instance_type
        self.security_group = security_group
        self.key_name = key_name
        self.user_data = user_data
        self.ami = ami or DEFAULT_AMI
        
        [region] = [i for i in boto.ec2.regions() if i.name == region_name]
        self.region = region
        self.availability_zone = availability_zone


class SpotInstanceLauncher(ScriptedInstanceLauncher):
    """Extends ScriptedInstanceLauncher to starting and stopping
    Spot instances"""

    spot_request_ids = []

    @property
    def instance_ids(self):
        requests = self.get_spot_requests()
        return [i.instance_id for i in requests if i.state == 'active']

    @property
    def bid_price(self):
        return get_most_recent_spot_price(self.instance_type)
    
    def get_request_statuses(self):
        return [(request.state, request.instance_id) for request in self.get_spot_requests()]

    def get_spot_requests(self):
        return self.ec2.get_all_spot_instance_requests(request_ids=self.spot_request_ids)

    def launch(self, num_instances, **kwargs):
        requests = self.ec2.request_spot_instances(
            self.bid_price,
            self.ami,
            count=num_instances,
            user_data=self.user_data,
            security_groups=[self.security_group],
            key_name=self.key_name,
            **kwargs
        )
        self.spot_request_ids.extend([request.id for request in requests])
                 
    def cancel(self, num_requests):
        all_requests = self.get_spot_requests()
        running_requests = [i for i in all_requests if i.instance_id]
        to_cancel = running_requests[:num_requests]
        self.ec2.cancel_spot_instance_requests([request.id for request in to_cancel])

        instance_ids = [request.instance_id for request in to_cancel] 
        if instance_ids:
            self.ec2.terminate_instances(instance_ids)


