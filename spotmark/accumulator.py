import os
import json
import time

import boto

from constants import INSTANCE_ID, SQS_QUEUE_NAME
import messaging

class SQSAccumulator(object):
    """Accumulates success and fail counts and periodically
    enqeues an update to SQS"""

    def __init__(self, queue_name=SQS_QUEUE_NAME):
        sqs = boto.connect_sqs()
        self.queue = sqs.get_queue(queue_name)
        self.success_count, self.failure_count = 0, 0
        self.last_sqs_time = None

    def enqueue(self, message):
        _message = {
            "instance_id": INSTANCE_ID,
            "content": message
        }    
        sqs_message = self.queue.new_message(body=json.dumps(_message))
        self.queue.write(sqs_message)

    def enqueue_update(self):
        now = int(time.time())

        self.enqueue({
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "interval_start": self.last_sqs_time,
            "interval_end": now
        })
        self.success_count, self.failure_count = 0, 0
        self.last_sqs_time = now

    def process_messages(self, messages):
        messages = [json.loads(msg) for msg in messages]
        self.success_count += sum(msg.get("success_count", 0) for msg in messages)
        self.failure_count += sum(msg.get("failure_count", 0) for msg in messages)

