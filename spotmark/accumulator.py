import os
import json
import time

import boto

import manager
from metadata import INSTANCE_ID
import messaging

LOG_FILE = 'accumulator.log'

class SQSAccumulator(object):
    """Accumulates success and fail counts and periodically
    enqeues an update to SQS"""

    success_count, fail_count = 0, 0
    last_sqs_time = None

    def __init__(self, queue_name=manager.SQS_QUEUE_NAME, update_interval_secs=10):
        sqs = boto.connect_sqs()
        self.queue = sqs.get_queue(queue_name)
        self.update_interval_secs = update_interval_secs        

    def enqueue(self, message):
        _message = {
            "instance_id": INSTANCE_ID,
            "content": message
        }    
        sqs_message = self.queue.new_message(body=json.dumps(_message))
        self.queue.write(sqs_message)

    def enqueue_update(self):
        timestamp = lambda: int(time.time())

        if not self.last_sqs_time:
            self.last_sqs_time = timestamp()
            return

        now = timestamp()

        self.enqueue({
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "interval_start": self.last_sqs_time,
            "interval_end": now
        })
        self.success_count, self.fail_count = 0, 0
        self.last_sqs_time = now

    def process_messages(self, messages):
    
        messages = [json.loads(msg) for msg in messages]
        self.success_count += sum(msg.get("success_count", 0) for msg in messages)
        self.fail_count += sum(msg.get("fail_count", 0) for msg in messages)

def start():

    accumulator = SQSAccumulator()
    streamer = messaging.ZMQPeriodicStreamer(
        accumulator.process_messages, accumulator.enqueue_update, 10000
    )

    accumulator.enqueue({"status": "running"})
    streamer.begin_streaming()

if __name__ == '__main__':
    start()
