import json
import unittest

import boto
import moto

from spotmark import accumulator, metadata

class TestSQSAccumulator(unittest.TestCase):

    def setUp(self):
        super(TestSQSAccumulator, self).setUp()

        self.mock = moto.mock_sqs()
        self.mock.start()
        self.queue = boto.connect_sqs().create_queue("test-queue")
        self.accumulator = accumulator.SQSAccumulator('test-queue')

    def tearDown(self):
        super(TestSQSAccumulator, self).tearDown()
        self.mock.stop()

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
    
        self.add_messages([10,5], [10,5])
        self.assertEqual(self.accumulator.success_count, 20)
        self.assertEqual(self.accumulator.failure_count, 10)

        self.add_messages([10,5], [10,5])
        self.assertEqual(self.accumulator.success_count, 40)
        self.assertEqual(self.accumulator.failure_count, 20)

    def test_enqueue(self):
        message = self.accumulator.queue.read()
        self.assertIsNone(message)

        data = {
            "success_count": 10,
            "failure_count": 10
        }
        self.accumulator.enqueue(data)

        sqs_message = self.accumulator.queue.read()
        message = json.loads(sqs_message.get_body())
        self.assertEquals(message["instance_id"], metadata.INSTANCE_ID)
        self.assertEquals(message["content"], data)

    def test_enqueue_update(self):
        self.add_messages([10,5], [10,5])
        self.accumulator.enqueue_update()

        sqs_message = self.accumulator.queue.read()
        self.assertIsNotNone(sqs_message)
        message = json.loads(sqs_message.get_body())
        content = message["content"]

        self.assertEqual(content["success_count"], 20)
        self.assertEqual(content["failure_count"], 10)
        self.assertIsNone(content["interval_start"])
        interval_end = content["interval_end"]
        self.assertEqual(interval_end, self.accumulator.last_sqs_time)

        self.add_messages([10,5], [10,5])
        self.accumulator.enqueue_update()

        sqs_message = self.accumulator.queue.read()
        self.assertIsNotNone(sqs_message)
        message = json.loads(sqs_message.get_body())
        content = message["content"]

        self.assertEqual(content["success_count"], 20)
        self.assertEqual(content["failure_count"], 10)
        self.assertEqual(content["interval_start"], interval_end)
        self.assertEqual(content["interval_end"], self.accumulator.last_sqs_time)

