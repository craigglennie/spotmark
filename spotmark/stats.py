from collections import namedtuple
import time

import boto

stats_tuple = namedtuple("stats", "successes failures requests start_time end_time interval")

class InstanceStats(object):

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
         

class StatsProvider(object):
    """Gets messages from running instances and
    calculates concurrency and success / failure rates"""

    

    def __init__(self, sqs_queue_name):
        self.queue = boto.connect_sqs().get_queue(sqs_queue_name)
        assert self.queue is not None, "Queue does not exist: %s" % sqs_queue_name

    
    
    
