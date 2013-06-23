import unittest

from spotmark.stats import InstanceStats, ClusterStats

class TestInstanceStats(unittest.TestCase):

    def setUp(self):

        self.stats = InstanceStats(1)
        self.stats.update(
            successes=1,
            failures=1,
            start_time=1,
            end_time=2,
        )
        self.stats.update(
            successes=1,
            failures=3,
            start_time=2,
            end_time=3,
        )

    def test_get_period(self):
        with self.assertRaisesRegexp(AssertionError, "min_time cannot be greater"):
            result = self.stats.get_period(10, 1)

        result = self.stats.get_period(1, 1)
        self.assertEqual(result, [])

        result = self.stats.get_period(0, 2)
        self.assertEqual(result, [self.stats._stats[0]]) 

        result = self.stats.get_period(1, 2)
        self.assertEqual(result, [self.stats._stats[0]]) 

        result = self.stats.get_period(2, 5)
        self.assertEqual(result, [self.stats._stats[1]]) 

        result = self.stats.get_period(2, 3)
        self.assertEqual(result, [self.stats._stats[1]]) 

        result = self.stats.get_period(0, 5)
        self.assertEqual(result, self.stats._stats) 

        result = self.stats.get_period(5, 10)
        self.assertEqual(result, []) 

    def test_success_rate(self):
        result = self.stats.success_rate(1, 1)
        self.assertEqual(result, 0)

        result = self.stats.success_rate(1, 2)
        self.assertEqual(result, 0.5)

        result = self.stats.success_rate(1, 3)
        self.assertEqual(result, 0.375)

    def test_request_count(self):
        result = self.stats.request_count(1, 1)
        self.assertEqual(result, 0)

        result = self.stats.request_count(1, 2)
        self.assertEqual(result, 2)

        result = self.stats.request_count(1, 3)
        self.assertEqual(result, 6)

class TestClusterStats(unittest.TestCase):

    def setUp(self):

        self.stats = ClusterStats()

        self.stats.update(
            instance_id=1,
            successes=1,
            failures=1,
            start_time=1,
            end_time=2,
        )

        self.stats.update(
            instance_id=2,
            successes=1,
            failures=3,
            start_time=2,
            end_time=3,
        )

    def test_get_period(self):
        with self.assertRaisesRegexp(AssertionError, "min_time cannot be greater"):
            result = self.stats.get_period(10, 1)

        result = self.stats.get_period(1, 1)
        self.assertEqual(result, [])

        result = self.stats.get_period(0, 2)
        self.assertEqual(result, [self.stats.instance_stats[1]]) 

        result = self.stats.get_period(1, 2)
        self.assertEqual(result, [self.stats.instance_stats[1]]) 

        result = self.stats.get_period(2, 5)
        self.assertEqual(result, [self.stats.instance_stats[2]]) 

        result = self.stats.get_period(2, 3)
        self.assertEqual(result, [self.stats.instance_stats[2]]) 

        result = self.stats.get_period(0, 5)
        self.assertEqual(result, self.stats.instance_stats.values()) 

        result = self.stats.get_period(5, 10)
        self.assertEqual(result, []) 

    def test_success_rate(self):
        result = self.stats.success_rate(1, 1)
        self.assertEqual(result, 0)

        result = self.stats.success_rate(1, 2)
        self.assertEqual(result, 0.5)

        result = self.stats.success_rate(1, 3)
        self.assertEqual(result, 0.375)

    def test_request_count(self):
        result = self.stats.request_count(1, 1)
        self.assertEqual(result, 0)

        result = self.stats.request_count(1, 2)
        self.assertEqual(result, 2)

        result = self.stats.request_count(1, 3)
        self.assertEqual(result, 6)
