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

    def test_get_required_instance_count(self):
        self.patch_cluster_stats("instance_count", 8)

        self.patch_cluster_stats("request_count", 80)
        count = self.launcher.get_required_instance_count()
        self.assertEqual(count, 10)

        self.patch_cluster_stats("request_count", 40)
        count = self.launcher.get_required_instance_count()
        self.assertEqual(count, 20)
    
        self.patch_cluster_stats("request_count", 160)
        count = self.launcher.get_required_instance_count()
        self.assertEqual(count, 5)

        

