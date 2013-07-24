import time

class LaunchStrategy(object):
    """Base class for an object implementing a strategy
    for deciding whether to launch instances"""

    def __init__(self, cluster_stats):
        self.cluster_stats = cluster_stats
        self.last_decision_time = 0
        self.last_decision = 0
        self.last_requests_per_second = 0

    def get_instance_count_delta(self):
        """Returns the adjustment to the current number of running instances
        that is required to achieve the desired requests per second"""
        raise NotImplementedError("Method should be implemented by sub-classes")

class RequestsPerSecondStrategy(LaunchStrategy):

    def __init__(self, cluster_stats, target_requests_per_second):
        super(RequestsPerSecondStrategy, self).__init__(cluster_stats)
        self.target_requests_per_second = target_requests_per_second
        self.required_instance_count = None

    def get_instance_count_delta(self):
        now = time.time()
        
        # Don't adjust number of machines because previous changes
        # are yet to take effect (eg new machines launching)
        instance_count = self.cluster_stats.instance_count(self.last_decision_time, now)
        if self.required_instance_count is not None and (self.required_instance_count != instance_count):
            return 0

        request_count = self.cluster_stats.request_count(self.last_decision_time, now)
        requests_per_instance = round(request_count / instance_count)
        self.required_instance_count = round(self.target_requests_per_second / requests_per_instance)

        return self.required_instance_count - instance_count
