import time
import unittest

from spotmark import launch_strategy

class TestRequestsPerSecondStrategy(unittest.TestCase):

    def patch_cluster_stats(self, func_name, value):
        setattr(self.launcher.cluster_stats, func_name, lambda *args: value)

    def setUp(self):
        class MockClusterStats(object):
            pass

        stats = MockClusterStats()
        self.launcher = launch_strategy.RequestsPerSecondStrategy(stats, 100)

    def test_get_instance_count_delta(self):
        instance_count = 8

        self.patch_cluster_stats("instance_count", instance_count)
        self.patch_cluster_stats("request_count", 80)
        # 80/8 = 10 requests per instance, 2 more instances required
        delta = self.launcher.get_instance_count_delta()
        self.assertEqual(delta, 2)

        instance_count += delta
        # 10 instances running
        self.patch_cluster_stats("instance_count", instance_count)
        self.patch_cluster_stats("request_count", 100)
        # 100 RPS achieved, no more instances required
        delta = self.launcher.get_instance_count_delta()
        self.assertEqual(delta, 0)
                
        self.patch_cluster_stats("request_count", 200)
        # 10 instances generating 20 RPS each, 10 instances running but only 5 required
        delta = self.launcher.get_instance_count_delta()
        self.assertEqual(delta, -5)
        instance_count += delta
        
        time.sleep(1)
        # Previous required instance count still doesn't match current
        # instance so wait until it does
        delta = self.launcher.get_instance_count_delta()
        self.assertEqual(delta, 0)

        # Instance count has adjusted to the specified level, so do nothing 
        time.sleep(1)
        self.patch_cluster_stats("instance_count", instance_count)
        self.patch_cluster_stats("request_count", self.launcher.target_requests_per_second)
        delta = self.launcher.get_instance_count_delta()
        self.assertEqual(delta, 0)

        # 80 RPS with 5 machines = 16 requests per instance; 100 / (80/5) = 6.25
        # but we can't launch .25 of a machine, so round to 1
        self.patch_cluster_stats("request_count", 80)
        delta = self.launcher.get_instance_count_delta()
        self.assertEqual(delta, 1)

