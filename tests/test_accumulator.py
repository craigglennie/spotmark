import json
import unittest

from spotmark import accumulator

class TestSQSAccumulator(unittest.TestCase):

    def setUp(self):
        self.accumulator = accumulator.SQSAccumulator()
    
    def add_messages(self, *counts):
        messages = []
        for success_count, failure_count in counts:
            json_str = json.dumps({
                "success_count": success_count,
                "failure_count": failure_count,
            })
            messages.append(json_str)

        self.accumulator.process_messages(messages)

    def test_process_messages(self):
        self.assertEqual(self.accumulator.success_count, 0)
        self.assertEqual(self.accumulator.failure_count, 0)
    
        self.add_messages([5,5], [5,5])
        self.assertEqual(self.accumulator.success_count, 10)
        self.assertEqual(self.accumulator.failure_count, 10)

        
