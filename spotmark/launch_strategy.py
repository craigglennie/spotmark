import time

class LaunchStrategy(object):
    """Base class for an object implementing a strategy
    for deciding whether to launch instances"""

    def __init__(self, cluster_stats):
        self.cluster_stats = cluster_stats
        self.last_decision_time = None

    def get_new_instance_count(self):
        raise NotImplementedError("Method should be implemented by sub-classes")

class RequestsPerSecondStrategy(LaunchStrategy):

    def __init__(self, cluster_stats, target_rps):
        super(RequestsPerSecondStrategy, self).__init__(cluster_stats)
        self.target_rps = target_rps

    def get_required_instance_count(self):
        """Returns the number of instances that should be running to achieve
        the desired requests per second"""
        now = time.time()
        
        request_count = self.cluster_stats.request_count(self.last_decision_time, now)
        instance_count = self.cluster_stats.instance_count(self.last_decision_time, now)
        requests_per_instance = round(request_count / instance_count)
        return self.target_rps / requests_per_instance
    
    

