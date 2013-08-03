import multiprocessing
import subprocess
import unittest
import time

from spotmark import ipc, constants

class EmitterProcess(multiprocessing.Process):
    
    def __init__(self, id, num_messages):
        super(EmitterProcess, self).__init__()
        self.id = id
        self.num_messages = num_messages
        self.sleep_between_messages_secs = 0

    def run(self):
        # Instantiaing the emitter in the constructor causes problems
        # because you can't create a context, then fork, and then use
        # the context - ZMQ will die
        zmq_emitter = ipc.ZMQEmitter(constants.ZMQ_URI)
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
        receiver = ipc.ZMQReceiver(self.messages_received, constants.ZMQ_URI)
        receiver.begin_receiving()        


class TestIPCBase(unittest.TestCase):
    """Integration tests for fan-in messaging with ZeroMQ.

    Creates a number of emitter processes all sending messages to a single
    receiver process. Receiver process requeues these messages for the test
    class to process."""

    def setUp(self):
        super(TestIPCBase, self).setUp()
        self.queue = multiprocessing.Queue()
        self.num_messages = 5
        self.messages = []
        self.num_emitters = 5
        self.emitters = [EmitterProcess(i, self.num_messages) for i in range(self.num_emitters)]
        self.receiver = None

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
            self.callback_interval_secs * 1000,
            constants.ZMQ_URI,
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
            # One quarter of callback_interval_secs to ensure that all emitters
            # will enqueue their ID at least once per callback interval
            emitter.sleep_between_messages_secs = 1
            emitter.start()

        have_validated_messages = False

        while 1:
            interval, messages = self.queue.get(timeout=10)

            # Interval will be None at the first call as it's the first enqueue,
            # but we do expect to see messages
            if interval is None:
                self.assertNotEqual(messages, [])
            else:
                self.assertEqual(interval, self.callback_interval_secs)

            # If we haven't received messages then the emitters have stopped sending
            # so we can exit successfully provided we have validated messages already
            if not messages:
                self.assertTrue(have_validated_messages)
                break

            emitter_ids = map(int, messages)
            for emitter in self.emitters:
                self.assertIn(emitter.id, emitter_ids)
            have_validated_messages = True
