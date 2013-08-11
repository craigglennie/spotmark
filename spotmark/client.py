#!/usr/bin/env python

import accumulator
import ipc
import constants

class Client(object):
    """Implements client functionality for Spotmark

    Listens to ZMQ event stream and periodically pushes
    totals to SQS"""

    def __init__(self, sqs_update_frequency_secs):
        self.sqs_update_frequency_secs = sqs_update_frequency_secs

    def start(self):

        sqs_accumulator = accumulator.SQSAccumulator()
        streamer = ipc.ZMQPeriodicReceiver(
            sqs_accumulator.process_messages, 
            sqs_accumulator.enqueue_update,
            self.sqs_update_frequency_secs * 1000,
            constants.ZMQ_URI
        )

        sqs_accumulator.enqueue({"status": "running"})
        streamer.begin_receiving()

if __name__ == '__main__':
    client = Client(10)
    client.start()


