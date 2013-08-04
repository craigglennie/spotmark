from datetime import datetime, timedelta
import boto
import time

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

class ScriptedInstanceLauncher(object):
    """Launches an EC2 instance to run a user-supplied script"""

    def __init__(self, instance_type, security_group, key_name, ami=None, user_data=None, region_name='us-east-1', availability_zone=None):
        self.instance_type = instance_type
        self.security_group = security_group
        self.key_name = key_name
        self.user_data = user_data
        self.ami = ami or DEFAULT_AMI

        [region] = [i for i in boto.ec2.regions() if i.name == region_name]
        self.region = region
        self.availability_zone = availability_zone

        self.instance_ids = set()
        self._ec2 = None

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

    def _update_instance_ids(self, reservation):
        """Updates the list of running instance IDs from a
        Reservation object.

        If instance IDs are not available yet (rare, but it does happen)
        will sleep and wait for them"""

        instances = reservation.instances
        if not instances:
            print "Instance IDs not available, waiting to get them"
            attempt = 1
            while attempt <= 4:
                time.sleep(15)
                for r in self.ec2.get_all_instances():
                    if r.id == reservation.id and r.instances:
                        instances = r.instances
                        break
                attempt += 1
            if not instances:
                print "Couldn't get instances for", reservation

        instance_ids = [i.id for i in instances]
        self.instance_ids.update(instance_ids)
        return instance_ids

    def launch(self, num_instances, **kwargs):
        reservation = self.ec2.run_instances(
            self.ami,
            min_count=num_instances,
            max_count=num_instances,
            key_name=self.key_name,
            user_data=self.user_data,
            security_groups=[self.security_group],
            instance_type=self.instance_type
        )
        return self._update_instance_ids(reservation)

    def terminate(self, num_instances=None, instance_ids=None):
        """Terminate the given number of instances, or terminate by instance_ids
        if supplied"""

        assert num_instances or instance_ids, "Must supply one of num_instances or instance_ids"

        if instance_ids:
            instance_ids = set(instance_ids)
            # Don't terminate instances we didn't launch
            if not instance_ids.issubset(self.instance_ids):
                unknown = list(instance_ids - self.instance_ids)
                raise AssertionError("Won't kill instances not launched by this object: %s" % unknown)
        else:
            instance_ids = list(self.instance_ids)[:num_instances]

        self.ec2.terminate_instances(list(instance_ids))
        self.instance_ids = self.instance_ids - set(instance_ids)


class SpotInstanceLauncher(ScriptedInstanceLauncher):
    """Extends ScriptedInstanceLauncher to starting and stopping
    Spot instances"""

    def __init__(self, user_data_script, region=None):
        super(SpotInstanceLauncher, self).__init__(user_data_script, region=region)
        self.spot_request_ids = []

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

    def stop(self, num_requests):
        all_requests = self.get_spot_requests()
        running_requests = [i for i in all_requests if i.instance_id]
        to_cancel = running_requests[:num_requests]
        self.ec2.cancel_spot_instance_requests([request.id for request in to_cancel])

        instance_ids = [request.instance_id for request in to_cancel] 
        if instance_ids:
            self.ec2.terminate_instances(instance_ids)


