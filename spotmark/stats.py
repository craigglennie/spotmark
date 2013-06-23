from collections import namedtuple
import time

import boto

stats_tuple = namedtuple("stats", "successes failures requests start_time end_time interval")

class InstanceStats(object):
    """Represents stats for a single benchmarking instance"""

    def __init__(self, instance_id):
        self.instance_id = instance_id
        self._stats = []

    def update(self, successes, failures, start_time, end_time):
        self._stats.append(stats_tuple(
            successes=successes,
            failures=failures,
            requests=successes + failures,
            start_time=start_time,
            end_time=end_time,
            interval=end_time - start_time
        ))

    def get_period(self, min_time, max_time):
        assert min_time <= max_time, "min_time cannot be greater than max_time"
        return [i for i in self._stats if i.start_time >= min_time and i.end_time <= max_time]

    def success_rate(self, min_time, max_time):
        """Returns the mean success rate of the instances
        for requests made over since last_seconds"""

        rates = [(i.successes / float(i.requests)) for i in self.get_period(min_time, max_time)]
        if not rates:
            return 0
        return sum(rates) / len(rates)

    def request_count(self, min_time, max_time):
        print [i.requests for i in self.get_period(min_time, max_time)] 
        return sum(i.requests for i in self.get_period(min_time, max_time))

         
class ClusterStats(object):
    """Provides stats for a cluster of benchmarking instances"""

    def __init__(self):
        self.instance_stats = {}

    def update(self, instance_id, successes, failures, start_time, end_time):
        if instance_id not in self.instance_stats:
            self.instance_stats[instance_id] = InstanceStats(instance_id)
        
        stats = self.instance_stats[instance_id]
        stats.update(successes, failures, start_time, end_time)

    def get_period(self, min_time, max_time):
        """Returns the set of InstanceStats objects which have data for the
        requested period"""

        assert min_time <= max_time, "min_time cannot be greater than max_time"
        return [i for i in self.instance_stats.values() if i.get_period(min_time, max_time)]

    def success_rate(self, min_time, max_time):
        """Returns the mean success rate of the instances
        for requests made over since last_seconds"""

        stats = [i.success_rate(min_time, max_time) for i in self.get_period(min_time, max_time)]
        if not stats:
            return 0
        return sum(stats) / len(stats)

    def request_count(self, min_time, max_time):
        return sum(i.request_count(min_time, max_time) for i in self.get_period(min_time, max_time))


