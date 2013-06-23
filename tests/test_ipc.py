import multiprocessing
import subprocess
import unittest
import time

from spotmark import ipc

class EmitterProcess(multiprocessing.Process):
    
    sleep_between_messages_secs = 0

    def __init__(self, id, num_messages):
        super(EmitterProcess, self).__init__()
        self.id = id
        self.num_messages = num_messages

    def run(self):
        # Instantiaing the emitter in the constructor causes problems
        # because you can't create a context, then fork, and then use
        # the context - ZMQ will die
        zmq_emitter = ipc.ZMQEmitter()
        sent = 0
        while 1: 
            zmq_emitter.send_string(str(self.id))
            time.sleep(self.sleep_between_messages_secs)
            sent += 1
            if sent == self.num_messages:
                break

class ReceiverProcess(multiprocessing.Process):

    def __init__(self, queue):
        super(ReceiverProcess, self).__init__(args=(queue,))
        
    def messages_received(self, messages):
        queue = self._args[0]
        queue.put(messages)

    def run(self):
        receiver = ipc.ZMQReceiver(self.messages_received)
        receiver.begin_receiving()        


class TestIPCBase(unittest.TestCase):
    """Integration tests for fan-in messaging with ZeroMQ.

    Creates a number of emitter processes all sending messages to a single
    receiver process. Receiver process requeues these messages for the test
    class to process."""

    num_messages = 5
    num_emitters = 5
    messages = []
    receiver = None

    def setUp(self):
        super(TestIPCBase, self).setUp()
        self.queue = multiprocessing.Queue()
        self.emitters = [EmitterProcess(i, self.num_messages) for i in range(self.num_emitters)]

    def tearDown(self):
        self.receiver.terminate()        
        for emitter in self.emitters:
            emitter.terminate()


class TestZMQReceiver(TestIPCBase):

    def test_ipc(self):
        self.receiver = ReceiverProcess(self.queue)
        self.receiver.start()

        for emitter in self.emitters:
            emitter.start()

        message_count = 0
        while 1:
            messages = self.queue.get(timeout=10)
            if messages:
                message_count += len(messages)
            if message_count == self.num_messages * len(self.emitters):
                break

class PeriodicReceiverProcess(multiprocessing.Process):

    def __init__(self, queue, callback_interval_secs):
        super(PeriodicReceiverProcess, self).__init__(args=(queue,))
        self.callback_interval_secs = callback_interval_secs
        self.messages = []
        self.last_periodic_time = None
 
    def msg_callback(self, messages):
        self.messages.extend(messages)

    def periodic_callback(self):
        interval = None
        current_time = int(time.time())
        if self.last_periodic_time:
            interval = current_time - self.last_periodic_time
        self.last_periodic_time = current_time

        message = (interval, self.messages)
        self.messages = []

        queue = self._args[0]
        queue.put(message)

    def run(self):
        receiver = ipc.ZMQPeriodicReceiver(
            self.msg_callback,
            self.periodic_callback,
            self.callback_interval_secs * 1000
        )
        receiver.begin_receiving()        

class TestZMQPeriodicReceiver(TestIPCBase):

    def setUp(self):
        super(TestZMQPeriodicReceiver, self).setUp()
        self.callback_interval_secs = 2

    def test_periodic_receiver(self):
        """Tests periodic receiver by having it accumulate IDs emitted by
        EmitterProcess and put them in the Queue at the frequency set by
        callback_interval_secs"""

        self.receiver = PeriodicReceiverProcess(self.queue, self.callback_interval_secs)
        self.receiver.start()

        for emitter in self.emitters:
            # Half of callback_interval_secs to ensure that all emitters
            # will enqueue their ID at least once per callback interval
            emitter.sleep_between_messages_secs = 1
            emitter.start()

        while 1:
            interval, messages = self.queue.get(timeout=10)
            if not messages:
                if not interval:
                    raise AssertionError("Expected some messages at first check")
                break

            if interval:
                self.assertEqual(interval, self.callback_interval_secs)
        
            emitter_ids = map(int, messages)
            for emitter in self.emitters:
                self.assertIn(emitter.id, emitter_ids)


            




